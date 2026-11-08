"""Transparent temporal-role correction; never change registered model/settings.

The registered all-other-session result is retained in robustness.json. This
separate analysis removes pre-training observations from out-of-time aggregates.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
import oos


def run(root):
    bundle,protocol=oos.check_frozen();manifest=oos.checked_inputs(root)
    inv=json.loads((oos.OUT/'inventory.json').read_text())
    registered=json.loads((oos.OUT/'robustness.json').read_text())
    cutoff=next(s['last_ns'] for s in inv['sessions'] if s['session_id']==oos.PILOT)
    excluded=[s['session_id'] for s in inv['sessions'] if s['role'] not in ['pilot_session_excluded','reserved_final'] and s['first_ns']<=cutoff]
    addendum=dict(created_utc=datetime.now(timezone.utc).isoformat(),reason='Pre-training44-second session cannot be called prospective/out-of-time validation',
        timing='Identified after registered robustness outcomes; not a pre-registered exclusion',
        rule='Only non-pilot, non-reserved sessions starting strictly after the entire original pilot session ended',
        cutoff_ns=cutoff,excluded_session_ids=excluded,original_robustness_sha256=oos.digest(oos.OUT/'robustness.json'),
        frozen_model_sha256=protocol['models_sha256'],source_sha256=oos.digest(__file__),
        unchanged='Feature/filter/model/threshold/metrics and first external validation remain unchanged; original all-role result preserved')
    path=oos.OUT/'chronology_addendum.json'
    if path.exists():
        previous=json.loads(path.read_text());addendum['created_utc']=previous['created_utc'];assert previous==addendum
    else:oos.save(path,addendum)
    kept={s['session_id'] for s in inv['sessions'] if s['role'] not in ['pilot_session_excluded','reserved_final'] and s['first_ns']>cutoff}
    pooled=defaultdict(list);history={};limits=defaultdict(dict);distribution=defaultdict(list)
    alternative=defaultdict(lambda:defaultdict(list));alt_history=defaultdict(dict);alt_limits=defaultdict(lambda:defaultdict(dict))
    for info in inv['sessions']:
        s=info['session_id']
        if s not in kept:continue
        rows=oos.read_session(root,manifest['sessions'][s],s)
        data,hist,lim,_=oos.session_data(rows,bundle['design'],s);history.update(hist)
        for t,r in hist.items():distribution[oos.date_of(t)].append(r['obi'])
        for h,records in data.items():pooled[h].extend(records);limits[h].update(lim[h])
        for name,change in [('ttl1s',{'maximum_receipt_age_seconds':1}),('lag500ms',{'maximum_exchange_receipt_lag_seconds':.5})]:
            data2,hist2,lim2,_=oos.session_data(rows,dict(bundle['design'],**change),s)
            alt_history[name].update(hist2)
            for h,records in data2.items():alternative[name][h].extend(records);alt_limits[name][h].update(lim2[h])
        for h,records in data.items():
            alternative['decision_every2s'][h].extend(r for r in records if ((r['time_ns']-lim[h][r['unit']][0])//oos.NS)%2==0)
            alt_limits['decision_every2s'][h].update(lim[h])
        print('chronological',s,flush=True)
    result={k:v for k,v in registered.items() if k in ['version','model_sha256','protocol_sha256']}
    result.update(correction=addendum,sessions=[s for s in registered['sessions'] if s['session_id'] in kept],
        retrospective_diagnostic_sessions=[s for s in registered['sessions'] if s['session_id'] in excluded],
        skipped=registered['skipped']+[dict(session_id=s,role='pretraining_diagnostic_only') for s in excluded],
        dates={},pooled={},sensitivity={},regimes={},feature_distributions={})
    for day,values in distribution.items():result['feature_distributions'][day]=dict(n=len(values),quantiles=np.quantile(values,[0,.1,.5,.9,1]).tolist(),histogram=np.histogram(values,bins=np.linspace(-1,1,21))[0].tolist())
    for h,data in pooled.items():
        hp=bundle['horizons'][str(h)]
        result['pooled'][str(h)]=oos.evaluate_cohort(data,hp,history,limits[h],sensitivity=True)
        for day in sorted(distribution):
            selected=[r for r in data if oos.date_of(r['time_ns'])==day];units={r['unit'] for r in selected}
            result['dates'].setdefault(day,{})[str(h)]=oos.evaluate_cohort(selected,hp,history,{u:v for u,v in limits[h].items() if u in units},sensitivity=True)
        p=oos.predict(data,hp,history);ret=np.array([r['forward_return'] for r in data]);y=(ret>0).astype(int)
        result['regimes'][str(h)]={}
        for field in ['spread_bps','lag_seconds','past_vol_bps']:
            threshold=hp[field+'_train_median'];groups={}
            for regime in ['low','high','unknown']:
                mask=np.array([(r.get(field) is None if regime=='unknown' else r.get(field) is not None and ((r[field]<=threshold) if regime=='low' else (r[field]>threshold))) for r in data]);direction=mask&(ret!=0)
                groups[regime]=dict(labels=int(mask.sum()),directional=int(direction.sum()),models={m:oos.metrics(y[direction],prob[direction]) if direction.any() else None for m,prob in p.items()})
            result['regimes'][str(h)][field]=dict(training_median_threshold=threshold,groups=groups)
    for name,by_h in alternative.items():
        result['sensitivity'][name]={str(h):oos.evaluate_cohort(data,bundle['horizons'][str(h)],alt_history[name] if name!='decision_every2s' else history,alt_limits[name][h]) for h,data in by_h.items()}
    assert oos.PILOT not in kept and protocol['reserved_final_session'] not in kept
    oos.check_frozen();oos.checked_inputs(root)
    oos.save(oos.OUT/'chronological_robustness.json',result)
    print('CHRONOLOGICAL ROBUSTNESS COMPLETE',len(kept),'sessions',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bbo-root',type=Path,required=True)
    run(parser.parse_args().bbo_root)
