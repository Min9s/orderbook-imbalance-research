"""Synthetic receipt-clock ambiguity tests; these are not market observations."""
from itertools import permutations
import hashlib
import json

import pytest

from obi_research import prepare
from obi_research.features import NS, prepare as frozen_prepare, targets
from test_research import CFG, row


def test_same_receipt_same_quote_different_exchange_times_cannot_change_population():
    first = row(1000, exchange=900)
    second = row(1000, exchange=800)
    expected = None
    for tied in permutations([first, second]):
        grid, records, audit, info = prepare(
            [row(0), *tied, row(2000, bid='100'), row(3000, bid='100')], CFG)
        assert [r is not None for r in records] == [True, False, True, True]
        labels = targets(grid, records, 1)
        assert [(r['time_ns'], r['label_end_ns']) for r in labels] == [(2*NS, 3*NS)]
        assert targets(grid, records, 2) == []
        actual = (grid.tolist(), records, audit, info, labels)
        if expected is None:
            expected = actual
        assert actual == expected


@pytest.mark.parametrize('conflict', ['quote', 'exchange_time', 'order_count', 'invalid_quote'])
def test_all_input_permutations_preserve_ambiguity_features_audits_and_labels(conflict):
    first = row(1000)
    if conflict == 'quote':
        second = row(1000, bid='100')
    elif conflict == 'exchange_time':
        second = row(1000, exchange=900)
    elif conflict == 'invalid_quote':
        second = row(1000, qb='0')
    else:
        second = row(1000)
        payload = json.loads(second['payload_json'])
        payload['bbo'][0]['n'] = 2
        second['payload_json'] = json.dumps(payload)
        second['event_id'] = hashlib.sha256(('bbo:'+json.dumps(
            payload, sort_keys=True, separators=(',', ':'))).encode()).hexdigest()
    inputs = [row(0), first, second, dict(first), row(2000, bid='100'), row(3000)]
    expected = None
    for shuffled in permutations(inputs):
        grid, records, audit, info = prepare(shuffled, CFG)
        assert [r is not None for r in records] == [True, False, True, True]
        assert audit['ambiguous_receipt_groups'] == 1
        assert audit['duplicate_event_id'] == 1
        assert audit['duplicate_receipt_timestamp'] == 1
        labels = [targets(grid, records, h) for h in (1, 2)]
        actual = (grid.tolist(), records, audit, info, labels)
        if expected is None:
            expected = actual
        assert actual == expected


def test_exact_duplicate_receipt_events_are_collapsed_without_ambiguity():
    grid, records, audit, info = prepare([row(0), row(0)], CFG)
    assert grid.tolist() == [0]
    assert records[0]['obi'] == .5 and records[0]['mid'] == 100
    assert audit['duplicate_event_id'] == 1
    assert audit.get('ambiguous_receipt_groups', 0) == 0
    assert info['events'] == 1
    assert info['receipt_interval_seconds_quantiles'] is None


def test_duplicate_replay_cannot_resolve_ambiguity_or_revive_an_older_quote():
    first = row(1000)
    replay = dict(first, ingested_at=2*NS)
    raw = [row(0), first, row(1000, bid='100'), replay,
           row(4000, bid='100'), row(5000, bid='100')]
    grid, records, audit, _ = prepare(raw, CFG)
    assert [r is not None for r in records] == [True, False, False, False, True, True]
    assert audit['duplicate_event_id'] == 1
    assert [r['time_ns'] for r in targets(grid, records, 1)] == [4*NS]
    assert targets(grid, records, 2) == []


def test_group_exchange_high_water_is_not_an_invented_within_tie_order():
    for tied in permutations([row(1000, exchange=900), row(1000, exchange=800)]):
        _, records, audit, _ = prepare([row(0), *tied, row(2000, exchange=850), row(3000)], CFG)
        assert [r is not None for r in records] == [True, False, False, True]
        # Only the later receipt group reverses the previously observed high water.
        assert audit['exchange_time_reversal'] == 1


def test_duplicate_event_is_still_payload_validated_before_deduplication():
    duplicate = row(0)
    duplicate['bid_sz'] = '999'
    with pytest.raises(ValueError, match='Payload quote mismatch'):
        prepare([row(0), duplicate, row(1000)], CFG)


def test_unambiguous_inputs_keep_frozen_feature_and_label_behavior():
    raw = [row(0), row(1000, bid='100'), row(2000, qb='0'),
           row(3000, bid='100'), row(4000, bid='100'), row(5000)]
    old = frozen_prepare(raw, CFG)
    new = prepare(raw, CFG)
    assert new[0].tolist() == old[0].tolist()
    assert new[1:] == old[1:]
    for horizon in (1, 2):
        assert targets(new[0], new[1], horizon) == targets(old[0], old[1], horizon)
