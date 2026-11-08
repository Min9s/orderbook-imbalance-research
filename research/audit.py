"""Post-MVP evaluation audit. Preserve pilot outputs and do not tune models.

Run after installing the project: python research/audit.py --bbo-dir /path/to/hour
"""
import argparse
from datetime import datetime, timezone, timedelta
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from obi_research.features import NS, prepare, quote_features, targets, split_masks
from obi_research.statistics import metrics

ROOT=Path(__file__).resolve().parents[1]


def load_rows(files):
    table=pq.read_table(files)
    for name in ['timestamp','ingested_at']:
        table=table.set_column(table.column_names.index(name),name,table[name].cast(pa.int64()))
    return table.to_pylist()


def summary(values):
    return dict(zip(['min','median','p95','max'],map(float,np.quantile(values,[0,.5,.95,1]))))


def price_change_baseline(rows, historical_grid, prior):
    """Sign of previous 1-second return; zero/missing -> TRAIN majority.

    No forward carry through gaps, no outcome-conditioned choice of fallback.
    """
    probabilities=[];states=[]
    for row in rows:
        previous=historical_grid.get(row['time_ns']-NS)
        if previous is None:
            probabilities.append(prior);states.append('missing_previous_grid')
        else:
            delta=row['mid']-previous['mid']
            probabilities.append(1. if delta>0 else 0. if delta<0 else prior)
            states.append('up' if delta>0 else 'down' if delta<0 else 'zero_previous_return')
    return np.array(probabilities),states


def bootstrap_audit(times,y,prob,base,*,start,end,seconds=60,offset=0,repeats=1000,seed=20261108):
    """Paired nonoverlapping CLOCK blocks including empty blocks.

    Anchored to fixed test interval (not first directional observation). Offset is
    an audit of grid alignment; boundary blocks are truncated, never wrapped.
    Same sampled blocks are used for both models. Fixed fitted-model uncertainty.
    """
    length=seconds*NS
    first=int(start-offset*NS)
    bounds=list(range(first,int(end)+1,length))
    groups=[np.flatnonzero((times>=max(a,start))&(times<min(a+length,end+1))) for a in bounds]
    counts=[len(g) for g in groups]
    rng=np.random.default_rng(seed)
    estimates={k:[] for k in ['accuracy','balanced_accuracy','roc_auc','accuracy_gain','balanced_accuracy_gain']}
    for _ in range(repeats):
        index=np.concatenate([groups[i] for i in rng.integers(0,len(groups),len(groups))])
        if not len(index):continue
        yy=y[index];p=prob[index];b=base[index]
        estimates['accuracy'].append(float(((p>=.5)==yy).mean()))
        estimates['accuracy_gain'].append(float((((p>=.5)==yy).astype(float)-((b>=.5)==yy)).mean()))
        if len(np.unique(yy))==2:
            # Avoid repeated sklearn validation for the simple two-class recalls.
            def ba(pp):return float(np.mean([((pp[yy==c]>=.5)==c).mean() for c in [0,1]]))
            estimates['balanced_accuracy'].append(ba(p))
            estimates['balanced_accuracy_gain'].append(ba(p)-ba(b))
            # AUC is computed through the same public metric, only when defined.
            from sklearn.metrics import roc_auc_score
            estimates['roc_auc'].append(float(roc_auc_score(yy,p)))
    return dict(block_seconds=seconds,offset_seconds=offset,blocks=len(groups),nonempty_blocks=sum(c>0 for c in counts),
        directional_observations_per_block=counts,
        blocks_with_both_classes=sum(len(np.unique(y[g]))==2 for g in groups if len(g)),
        valid_repeats={k:len(v) for k,v in estimates.items()},
        ci95={k:np.quantile(v,[.025,.975]).tolist() if v else None for k,v in estimates.items()})


def inventory_sessions(root):
    groups={}
    files=sorted(root.glob('*/*/*.parquet'))
    for path in files:
        t=pq.read_table(path,columns=['ingested_at','session_id','timestamp'])
        for s,rx,tx in zip(t['session_id'].to_pylist(),t['ingested_at'].cast(pa.int64()).to_pylist(),t['timestamp'].cast(pa.int64()).to_pylist()):
            r=groups.setdefault(s,dict(session_id=s,rows=0,first_ns=rx,last_ns=rx,files=set(),lag_min_ns=rx-tx,lag_max_ns=rx-tx))
            r['rows']+=1;r['first_ns']=min(r['first_ns'],rx);r['last_ns']=max(r['last_ns'],rx)
            r['files'].add(str(path));r['lag_min_ns']=min(r['lag_min_ns'],rx-tx);r['lag_max_ns']=max(r['lag_max_ns'],rx-tx)
    result=[]
    for r in sorted(groups.values(),key=lambda r:r['first_ns']):
        r['files']=len(r['files']);r['duration_seconds']=(r['last_ns']-r['first_ns'])/NS;result.append(r)
    return dict(file_count=len(files),sessions=result)



def heldout_quality(root, config, inventory):
    """Earliest >=30min session starting next UTC day; inspect no outcomes."""
    next_day=datetime.fromisoformat(config['date']).replace(tzinfo=timezone.utc)+timedelta(days=1)
    candidates=[r for r in inventory['sessions'] if r['first_ns']>=int(next_day.timestamp())*NS and r['duration_seconds']>=1800]
    candidate=min(candidates,key=lambda r:r['first_ns'])
    files=[]
    for hour in range(candidate['first_ns']//(3600*NS),candidate['last_ns']//(3600*NS)+1):
        day=datetime.fromtimestamp(hour*3600,timezone.utc)
        for path in sorted((root/day.strftime('%Y-%m-%d')/day.strftime('%H')).glob('*.parquet')):
            if candidate['session_id'] in pq.read_table(path,columns=['session_id'])['session_id'].to_pylist():files.append(path)
    rows=[r for r in load_rows(files) if r['session_id']==candidate['session_id']]
    grid,records,checks,session=prepare(rows,config)
    return dict(selection_rule='Earliest session starting on next UTC day with at least 30 minutes duration; no outcomes inspected',
        quality_only=True,session=session,audit=checks,valid_fraction=sum(r is not None for r in records)/len(records),
        sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bbo-dir',required=True,type=Path)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'results/audit')
    parser.add_argument('--inventory-root',type=Path,help='Optional BTC BBO root: metadata only, no return/model search')
    args=parser.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'research/design.json').read_text())
    files=sorted(args.bbo_dir.glob('*.parquet'))
    if not files:raise ValueError('No BBO Parquet inputs')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    rows=load_rows(files);grid,records,checks,session=prepare(rows,cfg)
    selected=sorted([r for r in rows if r['session_id']==session['session_id']],key=lambda r:r['ingested_at'])
    receipt=np.array([r['ingested_at'] for r in selected]);exchange=np.array([r['timestamp'] for r in selected])
    indexes=np.searchsorted(receipt,grid,side='right')-1
    sources=receipt[indexes]
    source_exchange=exchange[indexes]
    valid=np.array([r is not None for r in records])
    features_by_time={r['time_ns']:r for r in records if r}
    report=dict(session=session,checks=checks,input_sha256=hashes,
        exchange_timestamp_field_mismatches=sum(r['exchange_timestamp_ms']*1_000_000 != r['timestamp'] for r in selected),
        raw_file_rows=len(rows),selected_session_raw=len(selected),
        valid_quotes_before_dedup=sum(quote_features(r) is not None for r in selected),
        feature_event_rows=sum(quote_features(r) is not None for r in selected),
        latency_seconds=summary((receipt-exchange)/NS),
        feature_receipt_age_seconds=summary((grid[valid]-sources[valid])/NS),
        feature_exchange_age_seconds=summary((grid[valid]-source_exchange[valid])/NS),
        horizons={})
    tables=[]
    original=json.loads((ROOT/'results/summary.json').read_text())
    for h in cfg['horizons_seconds']:
        data=targets(grid,records,h)
        times=np.array([r['time_ns'] for r in data]);ends=np.array([r['label_end_ns'] for r in data])
        returns=np.array([r['forward_return'] for r in data]);y=(returns>0).astype(int);directional=returns!=0
        masks,bounds=split_masks(times,ends,int(grid[0]),int(grid[-1]))
        pre=[times<bounds[0],(times>=bounds[0])&(times<bounds[1]),times>=bounds[1]]
        splits={}
        for name,before,after in zip(['train','validation','test'],pre,masks):
            splits[name]=dict(before_purging=int(before.sum()),purged=int((before&~after).sum()),
                after_purging=int(after.sum()),zero_returns=int((after&~directional).sum()),
                directional=int((after&directional).sum()),down=int((after&directional&(y==0)).sum()),up=int((after&directional&(y==1)).sum()))
        train=masks[0]&directional;test=masks[2]&directional
        assert np.all(ends[masks[0]]<bounds[0]) and np.all(ends[masks[1]]<bounds[1])
        assert np.all(ends-times==h*NS) and np.all(sources[np.searchsorted(grid,times)]<=times)
        prior=float(y[train].mean());momentum,states=price_change_baseline(data,features_by_time,prior)
        probabilities=dict(baseline=np.full(len(data),prior),price_change=momentum)
        model_parameters={}
        for name,columns in [('obi',['obi']),('obi_spread_microprice',['obi','spread_bps','microprice_offset_bps'])]:
            x=np.array([[r[c] for c in columns] for r in data])
            model=make_pipeline(StandardScaler(),LogisticRegression(C=cfg['logistic_C'],max_iter=2000))
            model.fit(x[train],y[train]);probabilities[name]=model.predict_proba(x)[:,1]
            scaler,logistic=model.steps[0][1],model.steps[1][1]
            assert np.allclose(scaler.mean_,x[train].mean(axis=0))
            assert int(scaler.n_samples_seen_)==train.sum()
            model_parameters[name]=dict(scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist(),training_samples=int(train.sum()),coefficients=logistic.coef_.tolist(),intercept=logistic.intercept_.tolist())
        # Same exact frozen test timestamps/labels/probabilities as the MVP.
        with (ROOT/f'results/predictions_{h}s.csv').open() as f:frozen=list(csv.DictReader(f))
        assert [r['time_ns'] for r,m in zip(data,test) if m]==[int(r['time_ns']) for r in frozen]
        for name in ['baseline','obi','obi_spread_microprice']:
            assert np.allclose(probabilities[name][test],[float(r[name]) for r in frozen],rtol=0,atol=1e-12)
            assert metrics(y[test],probabilities[name][test])==original['horizons'][str(h)]['models'][name]['test']
        tstart=bounds[1];tend=int(grid[-1])-h*NS
        model_results={}
        for name,p in probabilities.items():
            model_results[name]=dict(metrics={label:metrics(y[m&directional],p[m&directional]) for label,m in zip(['train','validation','test'],masks)},bootstrap={})
            for seconds in [30,60,120]:
                for offset in [0,seconds//2]:
                    key=f'{seconds}s_offset{offset}'
                    model_results[name]['bootstrap'][key]=bootstrap_audit(times[test],y[test],p[test],probabilities['baseline'][test],start=tstart,end=tend,seconds=seconds,offset=offset)
            tables.append(dict(horizon_seconds=h,model=name,**model_results[name]['metrics']['test']))
        # Paired comparison with the causal trailing-price baseline, not just constant prior.
        price_comparison={str(s):bootstrap_audit(times[test],y[test],probabilities['obi'][test],momentum[test],start=tstart,end=tend,seconds=s) for s in [30,60,120]}
        gi=np.searchsorted(grid,times);target_gi=gi+h
        endpoint_after_start=sources[target_gi]>times
        nonzero=returns!=0
        # Label overlap diagnostics: successive nonzero targets are not independent moves.
        test_times=times[test];test_ends=ends[test]
        r=dict(candidate_grid_pairs=len(grid)-h,invalid_path_pairs=len(grid)-h-len(data),forward_labels=len(data),
            zero_returns=int((~directional).sum()),nonzero_before_purging=int(directional.sum()),splits=splits,
            purged_total=int((~np.logical_or.reduce(masks)).sum()),
            split_boundaries_ns=list(bounds),train_last_label_end_ns=int(ends[train].max()),
            validation_first_start_ns=int(times[masks[1]].min()),validation_last_label_end_ns=int(ends[masks[1]].max()),test_first_start_ns=int(times[test].min()),
            endpoint_quote_received_after_start=int(endpoint_after_start.sum()),endpoint_quote_not_after_start=int((~endpoint_after_start).sum()),
            nonzero_endpoint_not_after_start=int((~endpoint_after_start&nonzero).sum()),
            endpoint_receipt_after_target=int((sources[target_gi]>ends).sum()),
            endpoint_exchange_not_after_start=int((source_exchange[target_gi]<=times).sum()),
            nonzero_endpoint_exchange_not_after_start=int(((source_exchange[target_gi]<=times)&nonzero).sum()),
            nonzero_outcome_arrival_after_start_seconds=summary((sources[target_gi[nonzero]]-times[nonzero])/NS),
            target_receipt_age_seconds=summary((ends-sources[target_gi])/NS),
            effective_receipt_interval_seconds=summary((sources[target_gi]-sources[gi])/NS),
            nonzero_effective_receipt_interval_seconds=summary((sources[target_gi[nonzero]]-sources[gi[nonzero]])/NS),
            adjacent_test_label_overlap_count=int((test_times[1:]<test_ends[:-1]).sum()),
            test_price_baseline_states={state:sum(states[i]==state for i in np.flatnonzero(test)) for state in set(states)},
            models=model_results,model_parameters=model_parameters,obi_vs_price_baseline=price_comparison,
            frozen_pilot_predictions_verified=True)
        report['horizons'][str(h)]=r
    if args.inventory_root:
        inv=inventory_sessions(args.inventory_root)
        (out/'session_inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
        (out/'heldout_session_quality.json').write_text(json.dumps(heldout_quality(args.inventory_root,cfg,inv),indent=2)+'\n')
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[p.name] for p in files)
    report['code_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'src/obi_research/features.py',ROOT/'src/obi_research/statistics.py']}
    (out/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    with (out/'model_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(tables[0]));w.writeheader();w.writerows(tables)
    print(json.dumps(dict(selected_session_raw=report['selected_session_raw'],checks=checks,models=tables),indent=2))


if __name__=='__main__':main()
