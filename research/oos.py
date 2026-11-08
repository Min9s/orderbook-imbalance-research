"""Frozen-model external validation: inventory -> freeze -> first -> robustness.

All source market files are read-only. No training occurs in evaluation commands.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from obi_research.features import NS, prepare, quote_features, targets, split_masks
from obi_research.statistics import metrics
from audit import load_rows, price_change_baseline

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/oos'
PILOT='e29a1088ea904b0f83335013adb7c384'
FIRST='95a74716c1c140eb8e896cb11f924151'
MODELS=['baseline','price_change','obi','obi_spread_microprice']
COLS={'obi':['obi'],'obi_spread_microprice':['obi','spread_bps','microprice_offset_bps']}
DAY=86400*NS


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def csv_save(path,rows):
    if not rows:return
    with Path(path).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def iso(ns): return datetime.fromtimestamp(ns/NS,timezone.utc).isoformat()

def date_of(ns): return datetime.fromtimestamp(int(ns)//NS,timezone.utc).strftime('%Y-%m-%d')


def catalog(root):
    """File/receipt metadata only; no outcomes or performance-based selection."""
    groups=defaultdict(set); manifest=[]
    for p in sorted(root.glob('*/*/*.parquet')):
        for s in pq.read_table(p,columns=['session_id'])['session_id'].unique().to_pylist(): groups[s].add(str(p.relative_to(root)))
        manifest.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=digest(p)))
    return {s:sorted(paths) for s,paths in groups.items()},manifest


def read_session(root,paths,session):
    return [r for r in load_rows([root/p for p in paths]) if r['session_id']==session]


def annotate(grid,records,rows):
    """Add only causal diagnostic state. Past volatility never uses forward labels."""
    ordered=sorted(rows,key=lambda r:r['ingested_at'])
    receive=np.array([r['ingested_at'] for r in ordered],dtype=np.int64)
    exch=np.array([r['timestamp'] for r in ordered],dtype=np.int64)
    index=np.searchsorted(receive,grid,side='right')-1
    past_return=np.full(len(grid),np.nan)
    for i,r in enumerate(records):
        if r is None:continue
        r['session_id']=rows[0]['session_id']
        r['lag_seconds']=(receive[index[i]]-exch[index[i]])/NS
        if i and records[i-1] is not None:
            past_return[i]=np.log(r['mid']/records[i-1]['mid'])*10000
        # Require a full 60-second past window, all valid increments.
        window=past_return[max(0,i-59):i+1]
        r['past_vol_bps']=float(np.sqrt(np.mean(window**2))) if len(window)==60 and np.isfinite(window).all() else None
    return records


def inventory(root):
    OUT.mkdir(exist_ok=True)
    groups,manifest=catalog(root)
    cfg=json.loads((ROOT/'research/design.json').read_text())
    sessions=[];dates=defaultdict(Counter);seen={};global_duplicates=0;cross_session_duplicates=0
    pilot_summary=json.loads((ROOT/'results/summary.json').read_text())['session']
    pfirst,plast=pilot_summary['first_receipt_ns'],pilot_summary['last_receipt_ns']
    all_receipt_ranges=[]
    for s,paths in groups.items():
        rows=read_session(root,paths,s);ordered=sorted(rows,key=lambda r:r['ingested_at'])
        rx=np.array([r['ingested_at'] for r in ordered],dtype=np.int64)
        tx=np.array([r['timestamp'] for r in ordered],dtype=np.int64)
        lag=(rx-tx)/NS;gaps=np.diff(rx)/NS
        complete=sum(all(r.get(k) is not None for k in ['bid_px','ask_px','bid_sz','ask_sz']) for r in rows)
        numeric_valid=sum(quote_features(r) is not None for r in rows)
        crossed=sum(float(r['bid_px'])>float(r['ask_px']) for r in rows if r.get('bid_px') and r.get('ask_px'))
        local_duplicates=len(rows)-len({r['event_id'] for r in rows})
        cross=0
        for r in rows:
            if r['event_id'] in seen:
                global_duplicates+=1
                if seen[r['event_id']]!=s:cross+=1;cross_session_duplicates+=1
            else: seen[r['event_id']]=s
        counts=Counter(date_of(r['ingested_at']) for r in rows)
        try:
            grid,records,checks,_=prepare(rows,cfg)
            grid_counts=Counter(date_of(t) for t in grid)
            valid_counts=Counter(date_of(t) for t,r in zip(grid,records) if r is not None)
            error=None
        except (ValueError,TypeError,KeyError) as exc:
            grid=[];records=[];checks={};grid_counts={};valid_counts={};error=str(exc)
        item=dict(session_id=s,start_utc=iso(int(rx[0])),end_utc=iso(int(rx[-1])),
            first_ns=int(rx[0]),last_ns=int(rx[-1]),wall_seconds=float((rx[-1]-rx[0])/NS),rows=len(rows),
            dates=sorted(counts),rows_by_date=dict(counts),complete_quote_rows=complete,numeric_valid_quotes=numeric_valid,
            invalid_quote_ratio=1-numeric_valid/len(rows),crossed_quotes=crossed,duplicate_event_ids=local_duplicates,cross_session_duplicate_ids=cross,
            duplicate_receipts=int((np.diff(rx)==0).sum()),exchange_reversals=int((np.diff(tx)<0).sum()),
            exchange_timestamp_field_mismatches=sum(r['timestamp']!=r['exchange_timestamp_ms']*1_000_000 for r in rows),
            negative_lag=int((lag<0).sum()),lag_over_2s=int((lag>2).sum()),
            lag_quantiles_seconds=np.quantile(lag,[0,.5,.95,1]).tolist(),
            gaps_over_2s=int((gaps>2).sum()),max_gap_seconds=float(gaps.max()),
            grid_rows=len(grid),valid_grid_rows=sum(r is not None for r in records),valid_grid_by_date=dict(valid_counts),
            checks=checks,admission_error=error,
            overlap_pilot_interval_rows=int(((rx>=pfirst)&(rx<=plast)).sum()),
            original_session=s==PILOT)
        sessions.append(item);all_receipt_ranges.append((int(rx[0]),int(rx[-1]),s))
        for day,n in counts.items():
            dates[day].update(raw_rows=n,sessions=1,grid_rows=grid_counts.get(day,0),valid_grid_rows=valid_counts.get(day,0))
        print('inventory',s,len(rows),'valid grid',item['valid_grid_rows'],flush=True)
    sessions.sort(key=lambda r:r['first_ns']);all_receipt_ranges.sort()
    overlaps=[dict(first=a[2],second=b[2],overlap_seconds=(min(a[1],b[1])-b[0])/NS) for i,a in enumerate(all_receipt_ranges) for b in all_receipt_ranges[i+1:] if b[0]<=a[1]]
    last=max((s for s in sessions if s['session_id'] not in [PILOT,FIRST]),key=lambda r:r['last_ns'])['session_id']
    for s in sessions:
        s['role']='pilot_session_excluded' if s['session_id']==PILOT else 'first_external' if s['session_id']==FIRST else 'reserved_final' if s['session_id']==last else 'robustness'
    result=dict(file_count=len(manifest),raw_rows=sum(s['rows'] for s in sessions),session_count=len(sessions),
        distinct_receive_dates=len(dates),dates={d:dict(n) for d,n in sorted(dates.items())},
        cross_session_range_overlaps=overlaps,global_duplicate_event_ids=global_duplicates,cross_session_duplicate_event_ids=cross_session_duplicates,
        first_external_session=FIRST,reserved_final_session=last,sessions=sessions,
        inventory_fingerprint=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest())
    save(OUT/'inventory.json',result)
    save(OUT/'input_manifest.json',dict(files=manifest,sessions=groups))
    csv_save(OUT/'session_inventory.csv',[{k:v for k,v in s.items() if k not in ['rows_by_date','checks','valid_grid_by_date']} for s in sessions])
    csv_save(OUT/'date_inventory.csv',[dict(date=d,**dict(n)) for d,n in sorted(dates.items())])
    print('INVENTORY COMPLETE',result['raw_rows'],'rows;',len(dates),'dates; reserved',last,flush=True)


def frozen_probability(rows,model):
    x=np.array([[r[c] for c in model['columns']] for r in rows],dtype=float)
    z=((x-np.array(model['mean']))/np.array(model['scale']))@np.array(model['coef'])+model['intercept']
    return 1/(1+np.exp(-np.clip(z,-700,700)))


def freeze(root):
    """Only original training observations can reach fit(). Execute before evaluation."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    inv=json.loads((OUT/'inventory.json').read_text());manifest=checked_inputs(root)
    cfg=json.loads((ROOT/'research/design.json').read_text())
    files=sorted((root/cfg['date']/cfg['hour']).glob('*.parquet'))
    rows=load_rows(files);grid,records,_,_=prepare(rows,cfg)
    selected=[r for r in rows if r['session_id']==PILOT]
    annotate(grid,records,selected)
    bundle=dict(version='obi-external-v1',seed=cfg['seed'],design=cfg,training_session=PILOT,
        inventory_fingerprint=inv['inventory_fingerprint'],horizons={},python=platform.python_version(),
        original_training_files_sha256={str(p.relative_to(root)):digest(p) for p in files})
    np.random.seed(cfg['seed'])
    verified={}
    for h in cfg['horizons_seconds']:
        data=targets(grid,records,h)
        times=np.array([r['time_ns'] for r in data]);ends=np.array([r['label_end_ns'] for r in data]);ret=np.array([r['forward_return'] for r in data])
        masks,bounds=split_masks(times,ends,int(grid[0]),int(grid[-1]));train=masks[0]&(ret!=0);test=masks[2]&(ret!=0)
        y=(ret>0).astype(int);prior=float(y[train].mean())
        item=dict(prior=prior,train_directional=int(train.sum()),quantile_edges=np.unique(np.quantile([r['obi'] for r,m in zip(data,masks[0]) if m],[.2,.4,.6,.8])).tolist(),models={})
        for name,columns in COLS.items():
            x=np.array([[r[c] for c in columns] for r in data])
            estimator=make_pipeline(StandardScaler(),LogisticRegression(C=cfg['logistic_C'],max_iter=2000))
            estimator.fit(x[train],y[train]);scaler,lr=estimator.steps[0][1],estimator.steps[1][1]
            model=dict(columns=columns,mean=scaler.mean_.tolist(),scale=scaler.scale_.tolist(),coef=lr.coef_[0].tolist(),intercept=float(lr.intercept_[0]),classes=lr.classes_.tolist(),
                settings=dict(C=cfg['logistic_C'],max_iter=2000,solver='lbfgs',random_state=None))
            item['models'][name]=model
            with (ROOT/f'results/predictions_{h}s.csv').open() as f:original=list(csv.DictReader(f))
            p=frozen_probability(data,model)
            assert times[test].tolist()==[int(r['time_ns']) for r in original]
            assert np.allclose(p[test],[float(r[name]) for r in original],rtol=0,atol=1e-12)
            assert metrics(y[test],p[test])==json.loads((ROOT/'results/summary.json').read_text())['horizons'][str(h)]['models'][name]['test']
        for field in ['spread_bps','lag_seconds','past_vol_bps']:
            available=[r[field] for r,m in zip(data,masks[0]) if m and r.get(field) is not None]
            item[field+'_train_median']=float(np.median(available))
        bundle['horizons'][str(h)]=item
        verified[str(h)]=dict(original_test_predictions=True,train_rows=int(train.sum()),test_rows=int(test.sum()))
    core_files=[ROOT/'src/obi_research/features.py',ROOT/'src/obi_research/legacy_book.py',ROOT/'research/design.json',Path(__file__)]
    bundle['source_sha256']={str(p.relative_to(ROOT)):digest(p) for p in core_files}
    path=OUT/'frozen_models.json'
    if path.exists():
        assert json.loads(path.read_text())==bundle,'Existing frozen bundle differs; do not overwrite after outcome inspection'
    else: save(path,bundle)
    protocol=dict(version=bundle['version'],created_utc=datetime.now(timezone.utc).isoformat(),models_sha256=digest(path),
        inventory_sha256=digest(OUT/'inventory.json'),source_sha256=bundle['source_sha256'],pilot_reproduction=verified,
        first_external_session=FIRST,reserved_final_session=inv['reserved_final_session'],
        primary='First external session, 1s OBI balanced accuracy and paired BA gain over training-majority baseline',
        secondary='5s/10s, combined logistic, price-change baseline, quantile means and up probability; all disclosed',
        data_units='Receipt UTC day within session. Never join session paths. Drop labels crossing UTC date boundaries.',
        exclude='Entire pilot session excluded from external robustness; latest session reserved; all other sessions reported including empty/one-class results',
        zero_returns='Kept in statistical quantiles and class coverage; excluded from direction-model fit and scoring',
        timing='1s receipt-clock as-of; max receipt age2s, exchange-to-receipt lag[0,2]s; valid entire label path',
        fit='No new fit/preprocessing/threshold selection on external data; fitted parameter JSON only',
        baselines='Frozen original-training up prior; sign of previous1s return, zero/missing -> that prior',
        uncertainty='1000 paired nonoverlapping clock-block bootstrap replicates at30/60/120s, origin0 and half-block shift; stratify by session-date, retain empty time blocks; no date bootstrap',
        regimes='Causal trailing60s RMS past1s return (60 valid increments); spread/lag/vol low-high cutoffs from original training only; no parameter fitting on new sessions',
        sensitivity='Fixed additional diagnostics only: receipt TTL1s, exchange lag<=0.5s, decision every2s with exact1/5/10s endpoints. Primary remains unchanged.',
        interpretation='Only2 archived UTC dates and one new date; no independent28-day claim. Block intervals are exploratory conditional-on-model/session-composition; no multiple-testing correction or profitability claim.')
    proto=OUT/'protocol.json'
    if proto.exists():
        previous=json.loads(proto.read_text());protocol['created_utc']=previous['created_utc'];assert previous==protocol
    else:save(proto,protocol)
    print('FROZEN',digest(path),'protocol',digest(proto),'pilot reproduction',verified,flush=True)


def checked_inputs(root):
    manifest=json.loads((OUT/'input_manifest.json').read_text())
    for item in manifest['files']:
        if digest(root/item['path'])!=item['sha256']:raise ValueError('Source input changed: '+item['path'])
    return manifest


def sufficient_statistics(data,probabilities,edges):
    """Per-row additive statistics allow clock-block bootstrap without IID labels."""
    x=np.array([r['obi'] for r in data]);ret=np.array([r['forward_return']*10000 for r in data]);direction=ret!=0;up=ret>0;down=ret<0
    columns=dict(n=np.ones(len(data)),sx=x,sy=ret,sxx=x*x,syy=ret*ret,sxy=x*ret,nd=direction.astype(float),nu=up.astype(float),nl=down.astype(float))
    for name,p in probabilities.items():
        correct=(p>=.5)==up
        columns[name+'_correct']=(correct&direction).astype(float)
        columns[name+'_up']=(correct&up).astype(float)
        columns[name+'_down']=(correct&down).astype(float)
    quantile=np.searchsorted(edges,x,side='right')
    for q in range(len(edges)+1):
        choose=quantile==q
        columns[f'q{q}_n']=choose.astype(float);columns[f'q{q}_r']=np.where(choose,ret,0);columns[f'q{q}_up']=(choose&up).astype(float)
    return list(columns),np.column_stack(list(columns.values()))


def derive_stats(names,sums):
    a={name:sums[:,i] for i,name in enumerate(names)}
    def ratio(num,den):return np.divide(num,den,out=np.full_like(num,np.nan),where=den>0)
    denominator=np.sqrt(np.maximum(0,(a['n']*a['sxx']-a['sx']**2)*(a['n']*a['syy']-a['sy']**2)))
    result={'correlation':ratio(a['n']*a['sxy']-a['sx']*a['sy'],denominator)}
    for model in MODELS:
        result[model+'_accuracy']=ratio(a[model+'_correct'],a['nd'])
        result[model+'_balanced_accuracy']=(ratio(a[model+'_up'],a['nu'])+ratio(a[model+'_down'],a['nl']))/2
    for model in MODELS:
        for base in ['baseline','price_change']:
            for metric in ['accuracy','balanced_accuracy']:
                result[model+'_minus_'+base+'_'+metric]=result[model+'_'+metric]-result[base+'_'+metric]
    qs=[n[:-2] for n in names if n.startswith('q') and n.endswith('_n')]
    for q in qs:
        result[q+'_return_bps']=ratio(a[q+'_r'],a[q+'_n']);result[q+'_up_probability']=ratio(a[q+'_up'],a[q+'_n'])
    result['top_minus_bottom_return_bps']=result[qs[-1]+'_return_bps']-result[qs[0]+'_return_bps']
    return result


def clock_bootstrap(data,probabilities,edges,limits,seconds=60,offset=0,repeats=1000,seed=20261108):
    """Stratified session-date CLOCK blocks, empty blocks retained, fixed model.

    No day resampling: with two dates it would falsely imply between-day precision.
    The units remain separate and labels never cross their boundaries.
    """
    if not data:return None
    names,values=sufficient_statistics(data,probabilities,edges)
    times=np.array([r['time_ns'] for r in data],dtype=np.int64);units=np.array([r['unit'] for r in data])
    rng=np.random.default_rng(seed);samples=np.zeros((repeats,len(names)))
    blocks=0;nonempty=0;both=0;per_unit={}
    for unit,(start,end) in sorted(limits.items()):
        nblocks=(end-(start-offset*NS))//(seconds*NS)+1
        if nblocks<=0:continue
        chosen=np.flatnonzero(units==unit)
        index=(times[chosen]-(start-offset*NS))//(seconds*NS)
        agg=np.zeros((int(nblocks),len(names)))
        np.add.at(agg,index,values[chosen])
        b=int(nblocks);blocks+=b;nonempty+=int((agg[:,0]>0).sum())
        both+=int(((agg[:,names.index('nu')]>0)&(agg[:,names.index('nl')]>0)).sum())
        draws=rng.multinomial(b,np.full(b,1/b),size=repeats)
        samples+=draws@agg
        per_unit[unit]=b
    if blocks<4:return dict(blocks=blocks,nonempty_blocks=nonempty,ci95=None,reason='Fewer than four clock blocks')
    estimates=derive_stats(names,samples)
    ci={};valid={}
    for name,array in estimates.items():
        finite=array[np.isfinite(array)];valid[name]=len(finite)
        ci[name]=np.quantile(finite,[.025,.975]).tolist() if len(finite) else None
    return dict(block_seconds=seconds,offset_seconds=offset,blocks=blocks,nonempty_blocks=nonempty,blocks_with_both_classes=both,
        blocks_by_session_date=per_unit,repeats=repeats,valid_repeats=valid,ci95=ci,
        scope='Conditional on fitted model and observed session composition; exploratory, not between-day uncertainty')


def causal_price_probability(data,history,prior):
    values=[]
    for r in data:
        prev=history.get(r['time_ns']-NS)
        if prev is None or prev['session_id']!=r['session_id']:
            values.append(prior)
        else:
            change=r['mid']-prev['mid']
            values.append(1. if change>0 else 0. if change<0 else prior)
    return np.array(values)


def predict(data,hmodel,history):
    if not data:return {m:np.array([]) for m in MODELS}
    p={'baseline':np.full(len(data),hmodel['prior']),
       'price_change':causal_price_probability(data,history,hmodel['prior'])}
    for name,model in hmodel['models'].items():p[name]=frozen_probability(data,model)
    return p


def evaluate_cohort(data,hmodel,history,limits,*,sensitivity=False):
    p=predict(data,hmodel,history)
    ret=np.array([r['forward_return'] for r in data]);y=(ret>0).astype(int);d=ret!=0
    result=dict(labels=len(data),up=int((ret>0).sum()),down=int((ret<0).sum()),zero=int((ret==0).sum()),directional=int(d.sum()),
        models={name:metrics(y[d],prob[d]) if d.any() else None for name,prob in p.items()},
        correlation=float(np.corrcoef([r['obi'] for r in data],ret)[0,1]) if len(data)>2 and np.std(ret)>0 and np.std([r['obi'] for r in data])>0 else None,
        quantiles=[],bootstrap={})
    edges=hmodel['quantile_edges'];bins=np.searchsorted(edges,[r['obi'] for r in data],side='right')
    for q in range(len(edges)+1):
        choose=bins==q;n=int(choose.sum())
        result['quantiles'].append(dict(quantile=q+1,n=n,mean_return_bps=float(ret[choose].mean()*10000) if n else None,
            probability_up=float((ret[choose]>0).mean()) if n else None))
    means=[q['mean_return_bps'] for q in result['quantiles']]
    result['quantile_returns_nondecreasing']=all(b>=a for a,b in zip(means,means[1:])) if all(v is not None for v in means) else None
    configs=[(60,0)] if not sensitivity else [(seconds,offset) for seconds in [30,60,120] for offset in [0,seconds//2]]
    for seconds,offset in configs:
        result['bootstrap'][f'{seconds}s_offset{offset}']=clock_bootstrap(data,p,edges,limits,seconds,offset)
    return result


def session_data(rows,cfg,session_id):
    grid,records,checks,_=prepare(rows,cfg)
    annotate(grid,records,rows)
    history={r['time_ns']:r for r in records if r is not None}
    parts=defaultdict(list)
    for t in grid:parts[date_of(t)].append(int(t))
    all_data={};limits={}
    for h in cfg['horizons_seconds']:
        data=targets(grid,records,h)
        for r in data:r['unit']=session_id+'|'+date_of(r['time_ns'])
        # UTC-day crossing labels are explicitly removed, not used to link days.
        data=[r for r in data if date_of(r['time_ns'])==date_of(r['label_end_ns'])]
        all_data[h]=data
        limits[h]={session_id+'|'+day:(min(times),max(times)-h*NS) for day,times in parts.items() if max(times)-h*NS>=min(times)}
    return all_data,history,limits,checks


def check_frozen():
    bundle=json.loads((OUT/'frozen_models.json').read_text());protocol=json.loads((OUT/'protocol.json').read_text())
    assert digest(OUT/'frozen_models.json')==protocol['models_sha256']
    assert digest(OUT/'inventory.json')==protocol['inventory_sha256']
    for name,sha in protocol['source_sha256'].items():
        assert digest(ROOT/name)==sha,'Frozen evaluation code changed: '+name
    return bundle,protocol


def first_external(root):
    bundle,protocol=check_frozen();manifest=checked_inputs(root)
    inventory=json.loads((OUT/'inventory.json').read_text())
    info=next(s for s in inventory['sessions'] if s['session_id']==FIRST)
    pilot=next(s for s in inventory['sessions'] if s['session_id']==PILOT)
    assert info['first_ns']>pilot['last_ns'] and info['role']=='first_external'
    rows=read_session(root,manifest['sessions'][FIRST],FIRST)
    data,history,limits,checks=session_data(rows,bundle['design'],FIRST)
    result=dict(version=bundle['version'],model_sha256=protocol['models_sha256'],protocol_sha256=digest(OUT/'protocol.json'),
        session=info,admission_checks=checks,not_used_in_fit=True,role='first external, one new date only',horizons={})
    for h,records in data.items():
        result['horizons'][str(h)]=evaluate_cohort(records,bundle['horizons'][str(h)],history,limits[h],sensitivity=True)
        p=predict(records,bundle['horizons'][str(h)],history)
        # Aggregate empirical outputs are public; per-observation market data stay local.
        csv_save(ROOT/'data'/f'external_{h}s_predictions.csv',[dict(time_ns=r['time_ns'],label_end_ns=r['label_end_ns'],forward_return=r['forward_return'],**{k:float(v[i]) for k,v in p.items()}) for i,r in enumerate(records)])
    check_frozen();checked_inputs(root)
    save(OUT/'first_external.json',result)
    print('FIRST EXTERNAL COMPLETE',flush=True)
    for h,d in result['horizons'].items():print(h,d['labels'],d['directional'],{m:x['balanced_accuracy'] if x else None for m,x in d['models'].items()},flush=True)


def robustness(root):
    bundle,protocol=check_frozen();manifest=checked_inputs(root)
    if not (OUT/'first_external.json').exists():raise ValueError('Complete first external validation before robustness')
    inventory=json.loads((OUT/'inventory.json').read_text());cfg=bundle['design']
    pooled=defaultdict(list);histories={};limits_all=defaultdict(dict);session_results=[];sens=defaultdict(lambda:defaultdict(list));sens_limits=defaultdict(lambda:defaultdict(dict));sens_hist=defaultdict(dict)
    skipped=[];distribution=defaultdict(list)
    for info in inventory['sessions']:
        s=info['session_id']
        if info['role'] in ['pilot_session_excluded','reserved_final']:
            skipped.append(dict(session_id=s,role=info['role'],raw_rows=info['rows']));continue
        rows=read_session(root,manifest['sessions'][s],s)
        records,history,limits,checks=session_data(rows,cfg,s)
        histories.update(history)
        item=dict(session_id=s,role=info['role'],dates=info['dates'],raw_rows=info['rows'],quality=checks,horizons={})
        for t,r in history.items():distribution[date_of(t)].append(r['obi'])
        for h,data in records.items():
            pooled[h].extend(data);limits_all[h].update(limits[h])
            item['horizons'][str(h)]=evaluate_cohort(data,bundle['horizons'][str(h)],history,limits[h])
        session_results.append(item)
        # Tighter diagnostics: never loosen the primary filters, never refit.
        for name,change in [('ttl1s',{'maximum_receipt_age_seconds':1}),('lag500ms',{'maximum_exchange_receipt_lag_seconds':.5})]:
            alt=dict(cfg,**change);alt_data,alt_history,alt_limits,_=session_data(rows,alt,s)
            sens_hist[name].update(alt_history)
            for h,data in alt_data.items():sens[name][h].extend(data);sens_limits[name][h].update(alt_limits[h])
        for h,data in records.items():
            # Exact h-second endpoints remain; only decision starts are every2s.
            filtered=[r for r in data if ((r['time_ns']-limits[h][r['unit']][0])//NS)%2==0]
            sens['decision_every2s'][h].extend(filtered);sens_limits['decision_every2s'][h].update(limits[h])
        print('robustness',s,'raw',info['rows'],flush=True)
    result=dict(version=bundle['version'],model_sha256=protocol['models_sha256'],protocol_sha256=digest(OUT/'protocol.json'),
        skipped=skipped,sessions=session_results,dates={},pooled={},sensitivity={},feature_distributions={})
    for day,values in distribution.items():
        result['feature_distributions'][day]=dict(n=len(values),quantiles=np.quantile(values,[0,.1,.5,.9,1]).tolist(),histogram=np.histogram(values,bins=np.linspace(-1,1,21))[0].tolist())
    # Unit IDs accompany every row so no clock block can bridge a session/day gap.
    for h,data in pooled.items():
        result['pooled'][str(h)]=evaluate_cohort(data,bundle['horizons'][str(h)],histories,limits_all[h],sensitivity=True)
        for day in sorted(distribution):
            choose=[r for r in data if date_of(r['time_ns'])==day]
            units={r['unit'] for r in choose};lim={u:v for u,v in limits_all[h].items() if u in units}
            result['dates'].setdefault(day,{})[str(h)]=evaluate_cohort(choose,bundle['horizons'][str(h)],histories,lim,sensitivity=True)
    for name,by_h in sens.items():
        result['sensitivity'][name]={}
        for h,data in by_h.items():
            history=sens_hist[name] if name!='decision_every2s' else histories
            # Diagnostic metrics/retention only; no winning variant is selected.
            result['sensitivity'][name][str(h)]=evaluate_cohort(data,bundle['horizons'][str(h)],history,sens_limits[name][h])
    result['regimes']={}
    for h,data in pooled.items():
        hp=bundle['horizons'][str(h)];p=predict(data,hp,histories);ret=np.array([r['forward_return'] for r in data]);y=(ret>0).astype(int)
        result['regimes'][str(h)]={}
        for field in ['spread_bps','lag_seconds','past_vol_bps']:
            threshold=hp[field+'_train_median'];groups={}
            for regime in ['low','high','unknown']:
                mask=np.array([(r.get(field) is None if regime=='unknown' else r.get(field) is not None and ((r[field]<=threshold) if regime=='low' else (r[field]>threshold))) for r in data])
                direction=mask&(ret!=0)
                groups[regime]=dict(labels=int(mask.sum()),directional=int(direction.sum()),models={name:metrics(y[direction],prob[direction]) if direction.any() else None for name,prob in p.items()})
            result['regimes'][str(h)][field]=dict(training_median_threshold=threshold,groups=groups)
    check_frozen();checked_inputs(root)
    save(OUT/'robustness.json',result)
    print('ROBUSTNESS COMPLETE',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['inventory','freeze','first','robustness'])
    parser.add_argument('--bbo-root',required=True,type=Path)
    args=parser.parse_args()
    {'inventory':inventory,'freeze':freeze,'first':first_external,'robustness':robustness}[args.stage](args.bbo_root)
