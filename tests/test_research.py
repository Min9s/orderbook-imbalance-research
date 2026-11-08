import hashlib
import json
import numpy as np
import pytest
from obi_research.features import quote_features, prepare, targets, split_masks, NS
from obi_research.statistics import block_ci, metrics


def row(t,bid='99',ask='101',qb='3',qa='1',exchange=None):
    exchange=t if exchange is None else exchange
    p=dict(coin='BTC',time=exchange,bbo=[dict(px=bid,sz=qb,n=1),dict(px=ask,sz=qa,n=1)])
    identity=hashlib.sha256(('bbo:'+json.dumps(p,sort_keys=True,separators=(',',':'))).encode()).hexdigest()
    return dict(source='hyperliquid',coin='BTC',session_id='s',timestamp_basis='exchange',
        timestamp=exchange*1_000_000,ingested_at=t*1_000_000,event_id=identity,payload_json=json.dumps(p),
        bid_px=bid,ask_px=ask,bid_sz=qb,ask_sz=qa)


CFG=dict(maximum_receipt_age_seconds=2,maximum_exchange_receipt_lag_seconds=2)


def test_feature_numeric_identity_and_legacy_reuse():
    f=quote_features(row(0))
    assert f['mid']==100 and f['spread']==2 and f['obi']==.5
    assert f['microprice']==100.5 and f['relative_spread']==.02
    assert f['microprice_offset_bps']==pytest.approx(f['obi']*f['spread_bps']/2)


@pytest.mark.parametrize('kwargs',[dict(qb='0'),dict(qa='-1'),dict(bid='102'),dict(ask='nan')])
def test_invalid_quotes(kwargs):
    assert quote_features(row(0,**kwargs)) is None


def test_asof_never_uses_future_and_expires_old_state():
    g,r,a,_=prepare([row(100),row(4100,bid='100',ask='102')],CFG)
    assert g.tolist()==[NS,2*NS,3*NS,4*NS]
    assert r[0]['mid']==100 and r[1]['mid']==100
    assert r[2] is None and r[3] is None
    assert a['unusable_grid_rows']==2


def test_invalid_latest_does_not_revive_older_valid_quote():
    _,r,_,_=prepare([row(0),row(1000,qb='0'),row(2000,bid='100')],CFG)
    assert r[1] is None


def test_conflicting_receipt_ties_invalidated():
    _,r,a,_=prepare([row(0),row(1000),row(1000,bid='100'),row(2000)],CFG)
    assert r[1] is None and a['duplicate_receipt_timestamp']==1


def test_exchange_reversal_rejected_and_payload_tamper_fails():
    _,r,a,_=prepare([row(1000),row(2000,exchange=500),row(3000)],CFG)
    assert r[1] is None and a['exchange_time_reversal']==1
    bad=row(0);bad['bid_sz']='100'
    with pytest.raises(ValueError,match='mismatch'):prepare([bad],CFG)


def test_targets_exact_clock_and_no_gap_bridging():
    g=np.arange(4)*NS
    r=[dict(mid=x,time_ns=int(t)) for x,t in zip([100,101,102,104],g)]
    out=targets(g,r,2)
    assert out[0]['forward_return']==pytest.approx(np.log(102/100))
    assert out[0]['label_end_ns']==2*NS
    r[1]=None
    assert targets(g,r,2)==[]


def test_split_purges_endpoint_touching_boundary():
    t=np.arange(101)*NS;end=t+5*NS
    masks,bounds=split_masks(t,end,0,100*NS)
    assert all(end[masks[0]]<bounds[0])
    assert all(end[masks[1]]<bounds[1])
    assert not any(masks[0]&masks[1]) and not any(masks[1]&masks[2])
    assert not masks[0][55]


def test_block_interval_reproducible_and_auc_undefined():
    t=np.arange(300)*NS;x=np.sin(np.arange(300))
    assert block_ci(t,x,repeats=50)==block_ci(t,x,repeats=50)
    assert metrics(np.array([1,1]),np.array([.8,.8]))['roc_auc'] is None


def test_future_quote_cannot_change_existing_features():
    prefix=[row(0),row(1000,bid='100'),row(2000,bid='100')]
    g,r,_,_=prepare(prefix,CFG)
    _,extended,_,_=prepare(prefix+[row(3000,bid='1000',ask='1001')],CFG)
    assert r==extended[:len(g)]


def test_published_aggregate_metrics_and_optional_private_predictions():
    """Public: verify aggregate matrices; local: additionally audit private rows.

    Ranking AUC cannot be reconstructed from a confusion matrix. Event-level
    prediction CSVs are intentionally not required or redistributed publicly.
    """
    from pathlib import Path
    import csv
    root=Path(__file__).resolve().parents[1]
    summary=json.loads((root/'results/summary.json').read_text())
    for h,report in summary['horizons'].items():
        path=root/f'results/predictions_{h}s.csv'
        data=None
        if path.exists():
            with path.open() as f:data=list(csv.DictReader(f))
        for name,record in report['models'].items():
            result=record['test'];matrix=np.array(result['confusion_matrix'])
            assert matrix.sum()==result['n']
            assert np.trace(matrix)/matrix.sum()==result['accuracy']
            assert np.mean(np.diag(matrix)/matrix.sum(axis=1))==result['balanced_accuracy']
            assert result['roc_auc'] is None or 0<=result['roc_auc']<=1
            if data is not None:
                y=np.array([int(r['y']) for r in data])
                probability=np.array([float(r[name]) for r in data])
                assert metrics(y,probability)==result


def test_forward_label_uses_last_quote_before_endpoint_not_first_after():
    grid,records,_,_=prepare([row(0),row(900,bid='101',ask='103'),row(1100,bid='999',ask='1001')],CFG)
    label=targets(grid,records,1)[0]
    assert label['label_end_ns']==NS
    assert records[1]['mid']==102
    assert label['forward_return']==pytest.approx(np.log(102/100))
