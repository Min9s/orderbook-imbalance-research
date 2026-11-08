"""Final-stage analysis contracts; invented toy values are not market findings."""
import importlib.util
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('final_run',Path(__file__).resolve().parents[1]/'research/final_v1/run.py')
final=importlib.util.module_from_spec(spec);spec.loader.exec_module(final)


def test_zero_outcomes_remain_in_all_time_denominator():
    y=np.array([-1,0,1]);p=np.array([.1,.5,.9])
    forced=final.three_action(y,final.policy(p))
    gated=final.three_action(y,final.policy(p,True))
    assert forced['accuracy']==2/3 and forced['balanced_accuracy']==2/3
    assert gated['accuracy']==1 and gated['decision_coverage']==2/3
    assert forced['confusion_matrix']==[[1,0,0],[0,0,1],[0,0,1]]


def test_policy_band_is_fixed_and_uses_no_outcomes():
    assert final.policy(np.array([.39,.4,.5,.6,.61]),True).tolist()==[-1,0,0,0,1]


def test_all_time_moments_are_not_conditional_accuracy_or_pnl():
    data=[dict(obi=x,forward_return=r,forecast_mean_bps=f,spread_bps=.1,quantile=q,p_obi=p) for x,r,f,q,p in [(-.8,-.0001,-.2,0,.1),(0,0,0,2,.5),(.8,.0001,.2,4,.9)]]
    names,rows=final.moments(data)
    point=final.derived(names,rows.sum(axis=0,keepdims=True))
    assert point['flat'][0]==1/3
    assert point['forced_accuracy'][0]==2/3
    assert point['forecast_exceeds_spread'][0]==2/3
    assert point['forecast_exceeds_spread_plus1'][0]==0
    assert point['signed_markout'][0]==2/3


def test_delayed_markout_starts_after_one_second_and_keeps_original_feature():
    from test_research import row,CFG
    raw=[row(0),row(1000,bid='101',ask='103'),row(2000,bid='102',ask='104')]
    grid,records,_,_=final.prepare_session(raw,dict(design=CFG))
    data,_=final.delayed_data(grid,records,1,'s')
    assert len(data)==1 and data[0]['time_ns']==0
    assert data[0]['mid']==100
    assert data[0]['forward_return']==np.log(103/102)
    records[1]['source_exchange_ns']=0
    assert final.delayed_data(grid,records,1,'s')[0]==[]


def test_primary_and_exploratory_denominators_are_not_interchangeable():
    import json
    root=Path(__file__).resolve().parents[1]
    a=json.loads((root/'results/final_v1/primary_holdout.json').read_text())
    b=json.loads((root/'results/final_v1/exploration.json').read_text())
    for h,d in a['horizons'].items():
        e=b['holdout'][h]
        assert d['labels']==d['up']+d['down']+d['zero']==e['n']
        assert d['directional']==d['up']+d['down']
        assert np.isclose(e['three_action']['forced']['accuracy'],d['directional']/d['labels']*d['models']['obi']['accuracy'])
        assert np.isclose(e['three_action']['forced']['balanced_accuracy'],2/3*d['models']['obi']['balanced_accuracy'])
        for m in d['models'].values():assert np.array(m['confusion_matrix']).sum()==d['directional']


def test_holdout_consumption_and_registered_source_hashes_are_immutable():
    import json,hashlib
    root=Path(__file__).resolve().parents[1]
    protocol=json.loads((root/'results/final_v1/protocol.json').read_text())
    state=json.loads((root/'results/final_v1/consumption.json').read_text())
    assert state['status']=='complete' and state['seen_forever'] is True
    assert hashlib.sha256((root/'results/final_v1/primary_holdout.json').read_bytes()).hexdigest()==state['primary_sha256']
    assert hashlib.sha256((root/'research/final_v1/run.py').read_bytes()).hexdigest()==protocol['analysis_source_sha256']
    assert hashlib.sha256((root/'results/oos/frozen_models.json').read_bytes()).hexdigest()==protocol['models_sha256']


def test_second_first_disclosure_refuses_before_labeling(monkeypatch):
    import pytest
    monkeypatch.setattr(final,'checked',lambda:({},{}))
    monkeypatch.setattr(final.oos,'checked_inputs',lambda root:{})
    monkeypatch.setattr(final,'primary_record',lambda *a,**k:pytest.fail('Must not compute a new primary'))
    with pytest.raises(ValueError,match='already opened'):final.holdout(Path('/unused'))
