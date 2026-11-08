"""Frozen external evaluation contracts; all toy inputs are synthetic unit tests."""
from pathlib import Path
import sys
import importlib.util
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'))
spec=importlib.util.spec_from_file_location('oos',Path(__file__).resolve().parents[1]/'research/oos.py')
oos=importlib.util.module_from_spec(spec);spec.loader.exec_module(oos)


def test_frozen_prediction_is_pointwise_and_does_not_refit():
    model=dict(columns=['obi'],mean=[.1],scale=[.2],coef=[.3],intercept=.4)
    first=oos.frozen_probability([dict(obi=.5)],model)
    extended=oos.frozen_probability([dict(obi=.5),dict(obi=-100)],model)
    assert first[0]==extended[0]
    assert first[0]==1/(1+np.exp(-1))
    assert model['mean']==[.1]


def test_price_baseline_cannot_bridge_a_session_boundary():
    rows=[dict(session_id='new',time_ns=oos.NS,mid=100)]
    history={0:dict(session_id='old',mid=99)}
    assert oos.causal_price_probability(rows,history,.6).tolist()==[.6]
    history[0]['session_id']='new'
    assert oos.causal_price_probability(rows,history,.6).tolist()==[1.]


def test_sufficient_statistics_match_direction_metrics_and_quantiles():
    data=[dict(obi=-.8,forward_return=-.01),dict(obi=0.,forward_return=0.),dict(obi=.8,forward_return=.02)]
    probs={m:np.array([.1,.7,.9]) for m in oos.MODELS}
    names,matrix=oos.sufficient_statistics(data,probs,[-.5,0,.5])
    result=oos.derive_stats(names,matrix.sum(axis=0,keepdims=True))
    assert result['obi_accuracy'][0]==1
    assert result['obi_balanced_accuracy'][0]==1
    assert result['q0_return_bps'][0]==-100
    assert result['q3_up_probability'][0]==1
    assert result['obi_minus_baseline_accuracy'][0]==0


def test_clock_blocks_keep_session_gaps_outside_units_and_empty_blocks_inside():
    ns=oos.NS
    data=[dict(time_ns=ns,unit='a',obi=-.5,forward_return=-.01),dict(time_ns=901*ns,unit='b',obi=.5,forward_return=.01)]
    prob={m:np.array([.1,.9]) for m in oos.MODELS}
    # Two blocks per session: a long inter-session gap must NOT create13 blocks.
    limits={'a':(0,119*ns),'b':(900*ns,1019*ns)}
    r=oos.clock_bootstrap(data,prob,[0],limits,repeats=100)
    assert r['blocks']==4 and r['nonempty_blocks']==2
    assert r['blocks_by_session_date']=={'a':2,'b':2}
    assert r['ci95']['obi_minus_baseline_accuracy']==[0,0]
    assert r==oos.clock_bootstrap(data,prob,[0],limits,repeats=100)


def test_external_labels_do_not_cross_utc_midnight():
    from test_research import row, CFG
    rows=[row(86_399_000),row(86_400_000,bid='100',ask='102'),row(86_401_000,bid='101',ask='103')]
    data,_,_,_=oos.session_data(rows,dict(CFG,horizons_seconds=[1]),'s')
    assert len(data[1])==1
    assert oos.date_of(data[1][0]['time_ns'])==oos.date_of(data[1][0]['label_end_ns'])
    assert data[1][0]['time_ns']==86_400*oos.NS


def test_frozen_models_match_original_audited_coefficients():
    import json
    root=Path(__file__).resolve().parents[1]
    bundle=json.loads((root/'results/oos/frozen_models.json').read_text())
    original=json.loads((root/'results/audit/audit.json').read_text())
    for h,record in bundle['horizons'].items():
        for name,model in record['models'].items():
            old=original['horizons'][h]['model_parameters'][name]
            assert model['coef']==old['coefficients'][0]
            assert model['mean']==old['scaler_mean']
            assert model['scale']==old['scaler_scale']
            assert model['intercept']==old['intercept'][0]


def test_external_protocol_hashes_are_intact():
    import json
    root=Path(__file__).resolve().parents[1]
    protocol=json.loads((root/'results/oos/protocol.json').read_text())
    assert oos.digest(root/'results/oos/frozen_models.json')==protocol['models_sha256']
    assert oos.digest(root/'results/oos/inventory.json')==protocol['inventory_sha256']
    for file,sha in protocol['source_sha256'].items():assert oos.digest(root/file)==sha


def test_chronological_cohort_excludes_reserved_and_pretraining_sessions():
    import json
    root=Path(__file__).resolve().parents[1]
    inv=json.loads((root/'results/oos/inventory.json').read_text())
    result=json.loads((root/'results/oos/chronological_robustness.json').read_text())
    lookup={r['session_id']:r for r in inv['sessions']}
    cutoff=result['correction']['cutoff_ns']
    assert len(result['sessions'])==25
    for r in result['sessions']:
        assert lookup[r['session_id']]['first_ns']>cutoff
        assert r['session_id'] not in [oos.PILOT,inv['reserved_final_session']]
    assert len(result['retrospective_diagnostic_sessions'])==1
    for h,pool in result['pooled'].items():
        assert pool['directional']==sum(s['horizons'][h]['directional'] for s in result['sessions'])
        assert pool['labels']==sum(d[h]['labels'] for d in result['dates'].values())


def test_first_external_scores_are_unchanged_in_chronological_analysis():
    import json
    root=Path(__file__).resolve().parents[1]
    first=json.loads((root/'results/oos/first_external.json').read_text())
    result=json.loads((root/'results/oos/chronological_robustness.json').read_text())
    candidate=next(s for s in result['sessions'] if s['session_id']==oos.FIRST)
    for h,d in first['horizons'].items():
        other=candidate['horizons'][h]
        assert d['labels']==other['labels'] and d['models']==other['models']
        assert d['quantiles']==other['quantiles']
