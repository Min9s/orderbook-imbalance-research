"""Audit-specific checks; no changes to original eligibility or model conditions."""
from pathlib import Path
import importlib.util
import numpy as np

spec=importlib.util.spec_from_file_location('audit',Path(__file__).resolve().parents[1]/'research/audit.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_price_baseline_uses_past_only_with_explicit_fallback():
    ns=1_000_000_000
    history={0:dict(mid=100),ns:dict(mid=101),2*ns:dict(mid=101)}
    rows=[dict(time_ns=ns,mid=101,forward_return=-10),dict(time_ns=2*ns,mid=101),dict(time_ns=5*ns,mid=100)]
    prob,states=audit.price_change_baseline(rows,history,.6)
    assert prob.tolist()==[1,.6,.6]
    assert states==['up','zero_previous_return','missing_previous_grid']
    rows[0]['forward_return']=100
    history[100*ns]=dict(mid=100000)
    assert np.array_equal(prob,audit.price_change_baseline(rows,history,.6)[0])


def test_bootstrap_preserves_empty_clock_blocks_and_pairing():
    ns=1_000_000_000
    times=np.array([ns,2*ns,121*ns,122*ns])
    y=np.array([0,1,0,1]);prob=np.array([.2,.8,.2,.8])
    r=audit.bootstrap_audit(times,y,prob,prob,start=0,end=179*ns,seconds=60,repeats=50)
    assert r['blocks']==3 and r['nonempty_blocks']==2
    assert r['directional_observations_per_block']==[2,0,2]
    assert r['ci95']['accuracy_gain']==[0,0]
    assert r['ci95']['balanced_accuracy_gain']==[0,0]
    assert r==audit.bootstrap_audit(times,y,prob,prob,start=0,end=179*ns,seconds=60,repeats=50)
