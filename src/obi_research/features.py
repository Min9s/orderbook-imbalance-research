"""Receipt-causal L1 research; no delta reconstruction or execution inference."""
from collections import Counter
import hashlib
import json
import numpy as np
from .legacy_book import book_features

NS = 1_000_000_000


def quote_features(row):
    """Reuse original three features; impose stricter positive displayed sizes."""
    f = book_features(row)
    if f is None or min(float(row['bid_sz']), float(row['ask_sz'])) <= 0:
        return None
    bid, ask, qb, qa = [float(row[k]) for k in ('bid_px', 'ask_px', 'bid_sz', 'ask_sz')]
    mid = bid + (ask - bid) / 2
    micro = (ask * qb + bid * qa) / (qb + qa)
    return dict(f, mid=mid, spread=ask-bid, relative_spread=(ask-bid)/mid,
                microprice=micro, microprice_offset_bps=(micro-mid)/mid*10000)


def prepare(rows, config):
    """Validate payloads, choose longest session, invalidate suspect observations.

    Physical file ordering is not market ordering. Receipt ties with differing states
    and backwards exchange timestamps invalidate the current observation; no fallback.
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
    for r in selected:
        if (r['source'], r['coin'], r['timestamp_basis']) != ('hyperliquid', 'BTC', 'exchange'):
            raise ValueError('Unexpected source / coin / timestamp basis')
        p = json.loads(r['payload_json'])
        expected = hashlib.sha256(('bbo:'+json.dumps(p,sort_keys=True,separators=(',',':'))).encode()).hexdigest()
        if expected != r['event_id'] or p['coin'] != r['coin'] or p['time']*1_000_000 != r['timestamp']:
            raise ValueError('Payload identity/time mismatch')
        for side, level in zip(('bid','ask'),p['bbo'],strict=True):
            if level is None or any(str(level[k]) != r[f'{side}_{v}'] for k,v in [('px','px'),('sz','sz')]):
                raise ValueError('Payload quote mismatch')
        if r['event_id'] in seen:
            audit['duplicate_event_id'] += 1
            continue
        seen.add(r['event_id'])
        f=quote_features(r)
        if float(r['bid_px']) > float(r['ask_px']): audit['crossed'] += 1
        if min(float(r['bid_sz']),float(r['ask_sz'])) <= 0: audit['nonpositive_size'] += 1
        if f is None: audit['invalid_quote'] += 1
        lag=(r['ingested_at']-r['timestamp'])/NS
        if lag < 0 or lag > config['maximum_exchange_receipt_lag_seconds']:
            audit['invalid_clock_or_lag'] += 1
            f=None
        if r['timestamp'] < previous_exchange:
            audit['exchange_time_reversal'] += 1
            f=None
        previous_exchange=max(previous_exchange,r['timestamp'])
        if events and events[-1]['exchange_ns']==r['timestamp']: audit['duplicate_exchange_timestamp'] += 1
        event=dict(receipt_ns=r['ingested_at'],exchange_ns=r['timestamp'],features=f)
        if events and events[-1]['receipt_ns']==r['ingested_at']:
            audit['duplicate_receipt_timestamp'] += 1
            # Do not invent a within-tie ordering.
            if events[-1]['features'] != f: event['features']=None
            events[-1]=event
        else: events.append(event)
    times=np.array([e['receipt_ns'] for e in events],dtype=np.int64)
    gaps=np.diff(times)/NS
    audit['receipt_gaps_over_2s']=int((gaps>2).sum())
    first=((times[0]+NS-1)//NS)*NS
    grid=np.arange(first,times[-1]+1,NS,dtype=np.int64)
    indexes=np.searchsorted(times,grid,side='right')-1
    records=[]
    for clock,i in zip(grid,indexes,strict=True):
        event=events[i]
        age=(clock-event['receipt_ns'])/NS
        if event['features'] is None or age>config['maximum_receipt_age_seconds']:
            audit['unusable_grid_rows'] += 1
            records.append(None)
        else: records.append(dict(event['features'],time_ns=int(clock),receipt_age=age))
    audit['grid_rows']=len(grid)
    audit['valid_grid_rows']=sum(r is not None for r in records)
    return grid,records,dict(audit),dict(session_id=session,events=len(events),
        first_receipt_ns=int(times[0]),last_receipt_ns=int(times[-1]),
        receipt_interval_seconds_quantiles=np.quantile(gaps,[0,.5,.95,1]).tolist())


def targets(grid, records, horizon):
    """Exact clock-grid endpoints; reject any invalid intermediate grid state."""
    result=[]
    for i in range(len(records)-horizon):
        if any(r is None for r in records[i:i+horizon+1]): continue
        r=dict(records[i])
        r.update(label_end_ns=int(grid[i+horizon]),
                 forward_return=float(np.log(records[i+horizon]['mid']/r['mid'])))
        result.append(r)
    return result


def split_masks(times, ends, first, last):
    """Fixed elapsed-time 60/20/20 split, strict endpoint purging."""
    b1=first+int((last-first)*.6); b2=first+int((last-first)*.8)
    return ((times<b1)&(ends<b1), (times>=b1)&(times<b2)&(ends<b2), times>=b2), (b1,b2)
