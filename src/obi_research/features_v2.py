"""Conservative receipt-group preprocessing for new studies, separate from frozen v1."""
from collections import Counter
from itertools import groupby
import hashlib
import json

import numpy as np

from .features import NS, quote_features


def prepare(rows, config):
    """Collapse duplicate events; invalidate unordered groups of distinct events.

    No payload hash, exchange timestamp, price or physical row order breaks a
    receipt tie. Every row is validated, even a duplicate. Earliest receipt wins
    for repeated event IDs; duplicates cannot refresh or resolve an invalid state.
    """
    audit = Counter(raw_rows=len(rows))
    sessions = {}
    for row in rows:
        sessions.setdefault(row['session_id'], []).append(row['ingested_at'])
    session = max(sessions, key=lambda key: (max(sessions[key])-min(sessions[key]), key))
    selected = sorted((r for r in rows if r['session_id'] == session), key=lambda r:r['ingested_at'])
    audit['other_session_rows'] = len(rows)-len(selected)
    events, seen = [], set()
    previous_exchange = -1
    for receipt, group in groupby(selected, key=lambda r:r['ingested_at']):
        unique = {}
        for r in group:
            if (r['source'], r['coin'], r['timestamp_basis']) != ('hyperliquid', 'BTC', 'exchange'):
                raise ValueError('Unexpected source / coin / timestamp basis')
            payload = json.loads(r['payload_json'])
            expected = hashlib.sha256(('bbo:'+json.dumps(
                payload, sort_keys=True, separators=(',', ':'))).encode()).hexdigest()
            if (expected != r['event_id'] or payload['coin'] != r['coin']
                    or payload['time']*1_000_000 != r['timestamp']):
                raise ValueError('Payload identity/time mismatch')
            for side, level in zip(('bid', 'ask'), payload['bbo'], strict=True):
                if level is None or any(str(level[k]) != r[f'{side}_{v}']
                                        for k, v in [('px', 'px'), ('sz', 'sz')]):
                    raise ValueError('Payload quote mismatch')
            if r['event_id'] in seen or r['event_id'] in unique:
                audit['duplicate_event_id'] += 1
            unique[r['event_id']] = r
        fresh = [r for key, r in unique.items() if key not in seen]
        if not fresh:
            continue
        seen.update(unique)
        candidates = []
        # Compare each event only with earlier receipt groups. There is no known
        # order within this group, so reversal counters must not depend on one.
        for r in fresh:
            f = quote_features(r)
            if float(r['bid_px']) > float(r['ask_px']): audit['crossed'] += 1
            if min(float(r['bid_sz']), float(r['ask_sz'])) <= 0: audit['nonpositive_size'] += 1
            if f is None: audit['invalid_quote'] += 1
            lag = (receipt-r['timestamp'])/NS
            if lag < 0 or lag > config['maximum_exchange_receipt_lag_seconds']:
                audit['invalid_clock_or_lag'] += 1
                f = None
            if r['timestamp'] < previous_exchange:
                audit['exchange_time_reversal'] += 1
                f = None
            candidates.append(f)
        # This maximum is only a high-water mark for subsequent reversal checks;
        # it never selects a quote or asserts which tied event happened last.
        exchange = max(r['timestamp'] for r in fresh)
        previous_exchange = max(previous_exchange, exchange)
        if events and events[-1]['exchange_ns'] == exchange:
            audit['duplicate_exchange_timestamp'] += 1
        if len(unique) > 1:
            audit['duplicate_receipt_timestamp'] += len(unique)-1
            audit['ambiguous_receipt_groups'] += 1
            feature = None
        else:
            feature = candidates[0]
        events.append(dict(receipt_ns=receipt, exchange_ns=exchange, features=feature))
    times = np.array([e['receipt_ns'] for e in events], dtype=np.int64)
    gaps = np.diff(times)/NS
    audit['receipt_gaps_over_2s'] = int((gaps > 2).sum())
    first = ((times[0]+NS-1)//NS)*NS
    grid = np.arange(first, times[-1]+1, NS, dtype=np.int64)
    indexes = np.searchsorted(times, grid, side='right')-1
    records = []
    for clock, i in zip(grid, indexes, strict=True):
        event = events[i]
        age = (clock-event['receipt_ns'])/NS
        if event['features'] is None or age > config['maximum_receipt_age_seconds']:
            audit['unusable_grid_rows'] += 1
            records.append(None)
        else:
            records.append(dict(event['features'], time_ns=int(clock), receipt_age=age))
    audit['grid_rows'] = len(grid)
    audit['valid_grid_rows'] = sum(r is not None for r in records)
    return grid, records, dict(audit), dict(
        session_id=session, events=len(events), first_receipt_ns=int(times[0]),
        last_receipt_ns=int(times[-1]), receipt_interval_seconds_quantiles=(
            np.quantile(gaps, [0, .5, .95, 1]).tolist() if len(gaps) else None))
