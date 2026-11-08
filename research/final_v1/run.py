"""Final-v1: register before disclosure, consume once, then explore/replay.

No model fit exists here. Conditional Primary A and exploratory all-time B are
separate records. Old sources/results are read-only; private rows stay in data/.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.metrics import confusion_matrix,roc_auc_score

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research'))
import oos
from obi_research.features import NS,prepare,targets,split_masks

OUT=ROOT/'results/final_v1';PRIVATE=ROOT/'data/final_v1'
HOLDOUT='df37f36553464010ae9c34cd83d0eeac'
VERSION='obi-final-v1'


def safe(value):
    if isinstance(value,dict):return {str(k):safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [safe(v) for v in value]
    if isinstance(value,(np.integer,)):return int(value)
    if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
    if isinstance(value,np.bool_):return bool(value)
    return value


def save(path,value):oos.save(path,safe(value))


def read(path):return json.loads(Path(path).read_text())


def attach_clock(grid,records,raw):
    raw=sorted(raw,key=lambda r:r['ingested_at'])
    receive=np.array([r['ingested_at'] for r in raw],dtype=np.int64)
    index=np.searchsorted(receive,grid,side='right')-1
    for i,r in enumerate(records):
        if r is not None:
            r['source_receive_ns']=int(receive[index[i]])
            r['source_exchange_ns']=raw[index[i]]['timestamp']
    return records


def register(root):
    OUT.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
    bundle,old=oos.check_frozen();manifest=oos.checked_inputs(root)
    if (OUT/'protocol.json').exists():raise ValueError('Protocol already registered; do not revise after disclosure')
    if (OUT/'primary_holdout.json').exists():raise ValueError('Holdout already consumed')
    cfg=bundle['design'];files=sorted((root/cfg['date']/cfg['hour']).glob('*.parquet'))
    raw=oos.load_rows(files);grid,records,_,_=prepare(raw,cfg)
    mappings={}
    for h in cfg['horizons_seconds']:
        data=targets(grid,records,h);t=np.array([r['time_ns'] for r in data]);e=np.array([r['label_end_ns'] for r in data])
        masks,_=split_masks(t,e,int(grid[0]),int(grid[-1]));train=[r for r,m in zip(data,masks[0]) if m]
        edges=bundle['horizons'][str(h)]['quantile_edges'];bins=np.searchsorted(edges,[r['obi'] for r in train],side='right')
        means=[float(np.mean([r['forward_return']*10000 for r,b in zip(train,bins) if b==q])) for q in range(len(edges)+1)]
        classes=[int(np.sign(r['forward_return'])) for r in train]
        majority=max([-1,0,1],key=lambda c:classes.count(c))
        mappings[str(h)]=dict(bin_means_bps=means,bin_counts=[int((bins==q).sum()) for q in range(len(edges)+1)],
            training_all_labels=len(train),all_time_training_majority=majority,
            absolute_spread_training_median=float(np.median([r['spread'] for r in train])))
    inventory=read(oos.OUT/'inventory.json');hold=next(s for s in inventory['sessions'] if s['session_id']==HOLDOUT)
    assert old['reserved_final_session']==HOLDOUT and hold['rows']==77143
    prior=read(oos.OUT/'chronological_robustness.json');assert HOLDOUT not in [s['session_id'] for s in prior['sessions']]
    protocol=dict(version=VERSION,registered_utc=datetime.now(timezone.utc).isoformat(),holdout_session=HOLDOUT,
        models_sha256=oos.digest(oos.OUT/'frozen_models.json'),previous_protocol_sha256=oos.digest(oos.OUT/'protocol.json'),
        archive_fingerprint=inventory['inventory_fingerprint'],old_source_sha256=old['source_sha256'],
        analysis_source_sha256=oos.digest(__file__),training_only_magnitude_lookup=mappings,
        primary=dict(question='A: direction conditional on nonzero forward return',
            endpoint='1s frozen OBI Balanced Accuracy and paired BA gain versus original training-majority baseline',
            secondary='5s/10s, other original models, Accuracy/AUC/matrices and paired gains; same labels and filters',
            models='Unchanged saved parameters, preprocessing, feature order, C=1/lbfgs, threshold0.5; no fit',
            timing='Original1s receipt as-of, lag[0,2]s, receipt age<=2s, complete valid path, exact1/5/10s endpoints; no crossing sessions/dates',
            uncertainty='Original paired clock blocks30/60/120s and origin/half-block shifts,1000 replicates;60s main; no day bootstrap',
            coverage='Valid features/all grid states; valid forward labels/possible grid pairs; nonzero-label fraction is outcome coverage, not decision coverage'),
        exploratory=dict(question='B: information and decisions over all admissible labels, including unchanged prices',
            policies='Existing p>=0.5 forced up/down; fixed p>0.6 up,p<0.4 down,otherwise abstain; all-time original-training majority (flat) baseline',
            interpretation='p remains conditional-on-move; not an unconditional probability. Abstention coded0 only for descriptive three-action agreement, not a fitted flat-probability model',
            coverage='Ex-ante policy activity/valid feature states and activity/valid labels; direction-only subset is retrospective and separately identified',
            metrics='All-label up-vs-not-up rank AUC (not calibration), fixed three-class agreement/macro recall, unconditional quantile mean returns and up/down/zero probabilities; block intervals',
            magnitude='Five original-training all-label OBI-bin mean returns; separate exploratory lookup, not Logistic expected-return output',
            cost='Compare abs(training-bin forecast) and realized signed mid changes with current full spread_bps; hypothetical additional round-trip cost0/1/5bps; no fills/PnL',
            delay='Original features at t, benchmark log M(t+1+h)/M(t+1); both benchmark source receive AND exchange timestamps strictly after t; valid entire t..t+1+h path; no model/decision change',
            regimes='Original training spread_bps,lag,past60s-vol medians; also original-training absolute-spread median; no holdout-derived cutoffs',
            small_sessions='Report all sessions; additional sensitivity excluding sessions with fewer than100 nonzero1s labels in prior seen data; diagnostic, not winning-sample selection',
            uncertainty='Session-date-stratified60s paired time-block bootstrap for all-time moments; no between-day generalization or multiplicity-adjusted claim'),
        history='Primary and exploratory rules fixed before first final-holdout disclosure; after first scoring this holdout is permanently seen, even on replay')
    save(OUT/'protocol.json',protocol)
    print('REGISTERED',oos.digest(OUT/'protocol.json'),'model',protocol['models_sha256'],flush=True)


def checked():
    b,_=oos.check_frozen();p=read(OUT/'protocol.json')
    assert oos.digest(oos.OUT/'frozen_models.json')==p['models_sha256']
    assert oos.digest(__file__)==p['analysis_source_sha256'],'Registered analysis changed'
    return b,p


def session_rows(root,manifest,session):return oos.read_session(root,manifest['sessions'][session],session)


def prepare_session(raw,bundle):
    grid,records,checks,_=prepare(raw,bundle['design'])
    oos.annotate(grid,records,raw);attach_clock(grid,records,raw)
    hist={r['time_ns']:r for r in records if r is not None}
    return grid,records,hist,checks


def labeled(grid,records,h,session):
    data=targets(grid,records,h)
    for r in data:r['unit']=session+'|'+oos.date_of(r['time_ns'])
    data=[r for r in data if oos.date_of(r['time_ns'])==oos.date_of(r['label_end_ns'])]
    days=defaultdict(list)
    for t in grid:days[oos.date_of(t)].append(int(t))
    limits={session+'|'+d:(min(t),max(t)-h*NS) for d,t in days.items() if max(t)-h*NS>=min(t)}
    return data,limits


def augment(data,p,lookup,edges):
    for i,r in enumerate(data):
        q=int(np.searchsorted(edges,r['obi'],side='right'));r['quantile']=q
        r['forecast_mean_bps']=lookup['bin_means_bps'][q]
        for model,values in p.items():r['p_'+model]=float(values[i])
    return data


def primary_record(bundle,protocol,info,grid,records,history,checks):
    result=dict(version=VERSION,protocol_sha256=oos.digest(OUT/'protocol.json'),models_sha256=protocol['models_sha256'],session=info,
        quality=checks,status='Consumed holdout; never unused again',horizons={})
    for h in bundle['design']['horizons_seconds']:
        data,limits=labeled(grid,records,h,HOLDOUT);hp=bundle['horizons'][str(h)]
        result['horizons'][str(h)]=oos.evaluate_cohort(data,hp,history,limits,sensitivity=True)
        result['horizons'][str(h)]['coverage']=dict(valid_feature_states=len(history),grid_states=len(grid),
            feature_coverage=len(history)/len(grid),possible_forward_pairs=sum((end-start)//NS+1 for start,end in limits.values()),
            label_coverage=len(data)/sum((end-start)//NS+1 for start,end in limits.values()),
            nonzero_outcome_fraction=result['horizons'][str(h)]['directional']/len(data))
        p=oos.predict(data,hp,history);augment(data,p,protocol['training_only_magnitude_lookup'][str(h)],hp['quantile_edges'])
        pq.write_table(pa.Table.from_pylist(data),PRIVATE/f'holdout_{h}s.parquet')
    return result


def holdout(root,replay=False):
    bundle,protocol=checked();manifest=oos.checked_inputs(root)
    ledger=OUT/'consumption.json'
    if not replay:
        if ledger.exists():raise ValueError('Holdout already opened; replay is a reproducibility check, not a new test')
        save(ledger,dict(opened_utc=datetime.now(timezone.utc).isoformat(),status='started',protocol_sha256=oos.digest(OUT/'protocol.json'),seen_forever=True))
    else:
        if not (OUT/'primary_holdout.json').exists():raise ValueError('No consumed primary to replay')
    info=next(s for s in read(oos.OUT/'inventory.json')['sessions'] if s['session_id']==HOLDOUT)
    raw=session_rows(root,manifest,HOLDOUT);grid,records,history,checks=prepare_session(raw,bundle)
    result=primary_record(bundle,protocol,info,grid,records,history,checks)
    if replay:
        assert result==read(OUT/'primary_holdout.json'),'Replay differs from consumed result'
        save(OUT/'primary_replay.json',result)
    else:
        save(OUT/'primary_holdout.json',result)
        state=read(ledger);state['status']='complete';state['primary_sha256']=oos.digest(OUT/'primary_holdout.json');save(ledger,state)
    checked();oos.checked_inputs(root)
    print('PRIMARY '+('REPLAY MATCHED' if replay else 'HOLDOUT CONSUMED'),flush=True)
    for h,d in result['horizons'].items():print(h,d['labels'],d['directional'],d['models']['obi'],flush=True)


def policy(p,gate=False):
    return np.where(p>.6,1,np.where(p<.4,-1,0)) if gate else np.where(p>=.5,1,-1)


def three_action(y,action):
    n=len(y);cm=confusion_matrix(y,action,labels=[-1,0,1]) if n else np.zeros((3,3),dtype=int)
    return dict(n=n,accuracy=float(np.trace(cm)/n) if n else None,
        balanced_accuracy=float(np.mean(np.diag(cm)/cm.sum(axis=1))) if n and (cm.sum(axis=1)>0).all() else None,
        confusion_matrix=cm.tolist(),decision_coverage=float((action!=0).mean()) if n else None)


def moments(data,majority=0):
    ret=np.array([r['forward_return']*10000 for r in data]);y=np.sign(ret).astype(int);p=np.array([r['p_obi'] for r in data]);a=policy(p);g=policy(p,True)
    forecast=np.array([r['forecast_mean_bps'] for r in data]);spread=np.array([r['spread_bps'] for r in data]);side=np.sign(forecast)
    columns=dict(n=np.ones(len(data)),up=(y==1).astype(float),down=(y==-1).astype(float),flat=(y==0).astype(float),
        active=(g!=0).astype(float),signed_markout=a*ret,forecast_aligned_move=side*ret,spread=spread,forecast_abs=np.abs(forecast),
        realized_abs_exceeds_spread=(np.abs(ret)>spread).astype(float),forecast_exceeds_spread=(np.abs(forecast)>spread).astype(float))
    for cost in [1,5]:columns[f'forecast_exceeds_spread_plus{cost}']=(np.abs(forecast)>spread+cost).astype(float)
    for name,action in [('forced',a),('gated',g),('flat_baseline',np.full(len(y),majority))]:
        columns[name+'_correct']=(action==y).astype(float)
        for cls,label in [(-1,'down'),(0,'flat'),(1,'up')]:columns[name+'_'+label+'_correct']=((action==y)&(y==cls)).astype(float)
    for q in range(5):
        c=np.array([r['quantile']==q for r in data]);columns[f'q{q}_n']=c.astype(float)
        for name,value in [('ret',ret),('up',(y==1)),('down',(y==-1)),('flat',(y==0)),('spread',spread),('obi',np.array([r['obi'] for r in data]))]:columns[f'q{q}_{name}']=np.where(c,value,0)
    return list(columns),np.column_stack(list(columns.values()))


def derived(names,values):
    v={k:values[:,i] for i,k in enumerate(names)}
    def div(a,b):return np.divide(a,b,out=np.full_like(a,np.nan),where=b>0)
    result={name:div(v[name],v['n']) for name in ['up','down','flat','active','signed_markout','forecast_aligned_move','spread','forecast_abs','realized_abs_exceeds_spread','forecast_exceeds_spread','forecast_exceeds_spread_plus1','forecast_exceeds_spread_plus5']}
    for policy_name in ['forced','gated','flat_baseline']:
        result[policy_name+'_accuracy']=div(v[policy_name+'_correct'],v['n'])
        result[policy_name+'_ba']=sum(div(v[policy_name+'_'+c+'_correct'],v[c]) for c in ['down','flat','up'])/3
    for q in range(5):
        for name in ['ret','up','down','flat','spread','obi']:result[f'q{q}_{name}']=div(v[f'q{q}_{name}'],v[f'q{q}_n'])
    result['top_minus_bottom_return_bps']=result['q4_ret']-result['q0_ret']
    return result


def moment_ci(data,limits,majority,repeats=1000):
    if not data:return None
    names,array=moments(data,majority);t=np.array([r['time_ns'] for r in data]);u=np.array([r['unit'] for r in data]);rng=np.random.default_rng(20261108)
    samples=np.zeros((repeats,len(names)));blocks=0;nonempty=0
    for unit,(start,end) in sorted(limits.items()):
        n=int((end-start)//(60*NS)+1)
        if n<=0:continue
        chosen=np.flatnonzero(u==unit);index=(t[chosen]-start)//(60*NS);agg=np.zeros((n,len(names)));np.add.at(agg,index,array[chosen])
        blocks+=n;nonempty+=int((agg[:,0]>0).sum());samples+=rng.multinomial(n,np.full(n,1/n),size=repeats)@agg
    if blocks<4:return dict(blocks=blocks,ci95=None)
    estimates=derived(names,samples);ci={};valid={}
    for k,v in estimates.items():
        finite=v[np.isfinite(v)];ci[k]=np.quantile(finite,[.025,.975]).tolist() if len(finite) else None;valid[k]=len(finite)
    return dict(block_seconds=60,blocks=blocks,nonempty_blocks=nonempty,ci95=ci,valid_repeats=valid,scope='Conditional on observed session/date composition, not new-day precision')


def exploration_summary(data,lookup,limits,intervals=False):
    if not data:return dict(n=0)
    names,array=moments(data,lookup['all_time_training_majority']);point={k:float(v[0]) for k,v in derived(names,array.sum(axis=0,keepdims=True)).items()}
    ret=np.array([r['forward_return'] for r in data]);y=np.sign(ret).astype(int);p=np.array([r['p_obi'] for r in data]);forced=policy(p);gated=policy(p,True)
    action_models={}
    for model in oos.MODELS:
        mp=np.array([r['p_'+model] for r in data]);action_models[model]=dict(all_time_forced=three_action(y,policy(mp)),
            up_vs_not_up_rank_auc=float(roc_auc_score(y==1,mp)) if (y==1).any() and (y!=1).any() else None)
    result=dict(n=len(data),point=point,three_action=dict(forced=three_action(y,forced),gated=three_action(y,gated),
        flat_baseline=three_action(y,np.full(len(y),lookup['all_time_training_majority']))),
        model_all_time=action_models,nonzero_fraction=float((y!=0).mean()),
        lag_seconds_quantiles=np.quantile([r['lag_seconds'] for r in data],[0,.5,.95,1]).tolist(),
        receipt_age_seconds_quantiles=np.quantile([r['receipt_age'] for r in data],[0,.5,.95,1]).tolist())
    if intervals:result['uncertainty']=moment_ci(data,limits,lookup['all_time_training_majority'])
    return result


def delayed_data(grid,records,h,session):
    data,limits=labeled(grid,records,h+1,session);out=[]
    for r in data:
        i=int(np.searchsorted(grid,r['time_ns']));start=records[i+1];end=records[i+h+1]
        if any(q[k]<=r['time_ns'] for q in [start,end] for k in ['source_receive_ns','source_exchange_ns']):continue
        r['forward_return']=float(np.log(end['mid']/start['mid']));out.append(r)
    return out,limits


def explore(root):
    bundle,protocol=checked();manifest=oos.checked_inputs(root)
    if not (OUT/'primary_holdout.json').exists():raise ValueError('Primary holdout must be recorded first')
    groups={'holdout':HOLDOUT};seen_ids=[s['session_id'] for s in read(oos.OUT/'chronological_robustness.json')['sessions']]
    pooled=defaultdict(list);limits_all=defaultdict(dict);sessions=[];feature_coverage={};delayed=defaultdict(list);delayed_limits=defaultdict(dict)
    result=dict(version=VERSION,protocol_sha256=oos.digest(OUT/'protocol.json'),primary_sha256=oos.digest(OUT/'primary_holdout.json'),holdout={},seen_dates={},seen_pooled={},sessions=[],delayed={},regimes={},feature_coverage={})
    for session in seen_ids+[HOLDOUT]:
        raw=session_rows(root,manifest,session);grid,records,hist,checks=prepare_session(raw,bundle)
        entry=dict(session_id=session,role='consumed_final_holdout' if session==HOLDOUT else 'previously_seen_chronological',horizons={})
        role=entry['role']
        for h in bundle['design']['horizons_seconds']:
            hp=bundle['horizons'][str(h)];lookup=protocol['training_only_magnitude_lookup'][str(h)]
            data,lim=labeled(grid,records,h,session);augment(data,oos.predict(data,hp,hist),lookup,hp['quantile_edges'])
            d,l2=delayed_data(grid,records,h,session);augment(d,oos.predict(d,hp,hist),lookup,hp['quantile_edges'])
            feature_rows=list(hist.values());fp=oos.predict(feature_rows,hp,hist)['obi']
            coverage=dict(grid_states=len(grid),valid_features=len(hist),feature_coverage=len(hist)/len(grid) if len(grid) else None,
                policy_coverage_on_valid_features=float((policy(fp,True)!=0).mean()) if len(hist) else None,
                label_n=len(data),policy_coverage_on_valid_labels=float((policy(np.array([r['p_obi'] for r in data]),True)!=0).mean()) if data else None)
            entry['horizons'][str(h)]=dict(summary=exploration_summary(data,lookup,lim),coverage=coverage)
            if session==HOLDOUT:
                result['holdout'][str(h)]=exploration_summary(data,lookup,lim,True)
                result['feature_coverage'][str(h)]=coverage
                result['delayed'][str(h)]=dict(original_labels=len(data),delayed_labels=len(d),conditional=oos.evaluate_cohort(d,hp,hist,l2),all_time=exploration_summary(d,lookup,l2,True))
                # Small private plot arrays, not raw redistribution.
                pq.write_table(pa.Table.from_pylist(data),PRIVATE/f'holdout_{h}s.parquet')
            else:pooled[h].extend(data);limits_all[h].update(lim)
        sessions.append(entry);print('explore',session,flush=True)
    result['sessions']=sessions
    for h,data in pooled.items():
        hp=bundle['horizons'][str(h)];lookup=protocol['training_only_magnitude_lookup'][str(h)]
        result['seen_pooled'][str(h)]=exploration_summary(data,lookup,limits_all[h],True)
        for day in sorted({oos.date_of(r['time_ns']) for r in data}):
            selected=[r for r in data if oos.date_of(r['time_ns'])==day];units={r['unit'] for r in selected};lim={k:v for k,v in limits_all[h].items() if k in units}
            result['seen_dates'].setdefault(day,{})[str(h)]=exploration_summary(selected,lookup,lim,True)
        result['regimes'][str(h)]={}
        for field,threshold in [('spread_bps',hp['spread_bps_train_median']),('spread',lookup['absolute_spread_training_median']),('past_vol_bps',hp['past_vol_bps_train_median'])]:
            result['regimes'][str(h)][field]={}
            for group in ['low','high','unknown']:
                subset=[r for r in data if (r.get(field) is None if group=='unknown' else r.get(field) is not None and (r[field]<=threshold if group=='low' else r[field]>threshold))]
                result['regimes'][str(h)][field][group]=dict(threshold=threshold,summary=exploration_summary(subset,lookup,limits_all[h]))
        keep_ids={s['session_id'] for s in sessions if s['session_id']!=HOLDOUT and s['horizons']['1']['summary'].get('n',0) and s['horizons']['1']['summary']['nonzero_fraction']*s['horizons']['1']['summary']['n']>=100}
        large=[r for r in data if r['session_id'] in keep_ids];units={r['unit'] for r in large}
        result.setdefault('large_seen_sessions',{})[str(h)]=dict(session_count=len(keep_ids),summary=exploration_summary(large,lookup,{k:v for k,v in limits_all[h].items() if k in units},True))
    save(OUT/'exploration.json',result);checked();oos.checked_inputs(root)
    print('EXPLORATION COMPLETE',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['register','holdout','explore','replay']);parser.add_argument('--bbo-root',type=Path,required=True)
    args=parser.parse_args()
    from sklearn.linear_model import LogisticRegression
    def forbidden_fit(*a,**k):raise AssertionError('Final research attempted a model fit')
    LogisticRegression.fit=forbidden_fit
    {'register':register,'holdout':holdout,'explore':explore,'replay':lambda root:holdout(root,True)}[args.stage](args.bbo_root)
