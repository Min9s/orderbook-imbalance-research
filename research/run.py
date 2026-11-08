"""Reproduce the fixed first-hour BTC BBO pilot without touching source projects."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from obi_research.features import prepare, targets, split_masks, NS
from obi_research.statistics import metrics, block_ci


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,default=ROOT.parent/'Liquidation_gravity',help='Compatibility path to the original archive; no code imports from it')
    parser.add_argument('--bbo-dir',type=Path,help='Portable directory containing the 95 pilot BBO Parquet files')
    parser.add_argument('--recorder-dir',type=Path,help='Portable directory with status.json and events.jsonl')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'results',help='Separate output preserves the recorded pilot results')
    args=parser.parse_args()
    cfg=json.loads((ROOT/'research/design.json').read_text())
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    source=args.source_root.resolve()
    folder=(args.bbo_dir or source/'data/raw/hyperliquid/bbo/BTC'/cfg['date']/cfg['hour']).resolve()
    files=sorted(folder.glob('*.parquet'))
    if not files:raise ValueError(f'No real BBO files in {folder}')
    inventory=[dict(path=f"data/raw/hyperliquid/bbo/BTC/{cfg['date']}/{cfg['hour']}/{p.name}",bytes=p.stat().st_size,
                    sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
    manifest_path=output/'input_manifest.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text())['files'] != inventory:
        raise ValueError('Input inventory differs from the recorded run; use a separate project/output for a new study')
    table=pq.read_table(files)
    for c in ['timestamp','ingested_at']:
        table=table.set_column(table.column_names.index(c),c,table[c].cast(pa.int64()))
    grid,records,audit,session=prepare(table.to_pylist(),cfg)
    evidence_dir=args.recorder_dir or source/'data/interim/market_recorder/d7830102b0a24e6c9d27bc2ec21d8910'
    evidence={}
    for name in ['status.json','events.jsonl']:
        path=evidence_dir/name
        evidence[name]=dict(path=f'data/interim/market_recorder/{evidence_dir.name}/{name}',sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    # Local derived artifact for inspection; original files remain required for full audit replay.
    pq.write_table(pa.Table.from_pylist([r for r in records if r]),output/'clock_features.parquet')
    summary=dict(config=cfg,audit=audit,session=session,horizons={},
        input_inventory_sha256=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest())
    valid=[r for r in records if r]
    obi=np.array([r['obi'] for r in valid])
    summary['obi_quantiles']=np.quantile(obi,[0,.1,.5,.9,1]).tolist()
    summary['spread_obi_correlation']=float(np.corrcoef(obi,[r['spread_bps'] for r in valid])[0,1])
    summary['obi_lag1_autocorrelation']=float(np.corrcoef(obi[:-1],obi[1:])[0,1])
    fig,ax=plt.subplots(figsize=(7,4));ax.hist(obi,bins=40,color='#226e88')
    ax.set(xlabel='L1 order book imbalance',ylabel='1-second observations',title='Hyperliquid BTC | first stored hour, longest session')
    fig.tight_layout();fig.savefig(output/'obi_histogram.png',dpi=160);plt.close(fig)
    qfig,qax=plt.subplots(figsize=(7,4));pfig,pax=plt.subplots(figsize=(7,4))
    all_metrics=[];quantile_rows=[]
    for horizon in cfg['horizons_seconds']:
        rows=targets(grid,records,horizon)
        times=np.array([r['time_ns'] for r in rows]);ends=np.array([r['label_end_ns'] for r in rows])
        ret=np.array([r['forward_return'] for r in rows]);x=np.array([r['obi'] for r in rows])
        masks,bounds=split_masks(times,ends,int(grid[0]),int(grid[-1]))
        # Quantile edges estimated on training features only, no rank tie splitting.
        edges=np.unique(np.quantile(x[masks[0]],[.2,.4,.6,.8]))
        bins=np.searchsorted(edges,x,side='right')
        def corr_stat(sample):
            return np.corrcoef(sample[:,0],sample[:,1])[0,1]
        result=dict(labeled_rows=len(rows),zero_returns=int((ret==0).sum()),
            correlation=float(np.corrcoef(x,ret)[0,1]),quantile_edges=edges.tolist(),
            split_boundaries_ns=list(bounds),purged_rows=int((~np.logical_or.reduce(masks)).sum()),
            split_counts_all=[int(m.sum()) for m in masks],models={},quantiles=[],
            correlation_ci={})
        for seconds in cfg['bootstrap_block_seconds']:
            result['correlation_ci'][str(seconds)]=block_ci(times,np.column_stack([x,ret]),corr_stat,seconds=seconds)
        for b in range(len(edges)+1):
            select=bins==b
            mean=float(ret[select].mean()*10000);prob=float((ret[select]>0).mean())
            ci=block_ci(times,np.where(select,ret*10000,np.nan),np.nanmean)
            pci=block_ci(times,np.where(select,(ret>0).astype(float),np.nan),np.nanmean)
            q=dict(horizon_seconds=horizon,quantile=b+1,n=int(select.sum()),mean_return_bps=mean,
                probability_up_including_zero=prob,return_ci95=ci,probability_ci95=pci)
            result['quantiles'].append(q);quantile_rows.append(q)
        qs=result['quantiles'];xx=np.arange(1,len(qs)+1)
        for ax,key,cikey in [(qax,'mean_return_bps','return_ci95'),(pax,'probability_up_including_zero','probability_ci95')]:
            yy=np.array([q[key] for q in qs]);ci=np.array([q[cikey] for q in qs])
            # Bootstrap percentiles need not enclose the point estimate; draw endpoints directly.
            line=ax.plot(xx,yy,'o-',label=f'{horizon}s')[0]
            ax.vlines(xx,ci[:,0],ci[:,1],color=line.get_color(),alpha=.5)
        directional=ret!=0;y=(ret>0).astype(int)
        result['directional_split_counts']=[int((m&directional).sum()) for m in masks]
        if any(len(np.unique(y[m&directional]))<2 for m in masks):
            result['model_skip_reason']='Insufficient classes in a chronological split'
        else:
            train=masks[0]&directional
            prior=float(y[train].mean())
            predictors={
                'baseline':None,
                'obi':['obi'],
                'obi_spread_microprice':['obi','spread_bps','microprice_offset_bps']}
            probabilities={}
            for name,features in predictors.items():
                if features:
                    matrix=np.array([[r[k] for k in features] for r in rows])
                    model=make_pipeline(StandardScaler(),LogisticRegression(C=cfg['logistic_C'],max_iter=2000))
                    model.fit(matrix[train],y[train]);prob=model.predict_proba(matrix)[:,1]
                else:prob=np.full(len(rows),prior)
                probabilities[name]=prob
                result['models'][name]={}
                for split,m in zip(['train','validation','test'],masks,strict=True):
                    choose=m&directional;record=metrics(y[choose],prob[choose])
                    result['models'][name][split]=record
                    all_metrics.append(dict(horizon_seconds=horizon,model=name,split=split,**record))
                test=masks[2]&directional
                delta=((prob[test]>=.5)==y[test]).astype(float)-((probabilities['baseline'][test]>=.5)==y[test])
                result['models'][name]['test_accuracy_gain_ci95']={str(s):block_ci(times[test],delta,seconds=s) for s in cfg['bootstrap_block_seconds']}
            # Raw test probabilities enable independent metric reproduction.
            test=masks[2]&directional
            write_csv(output/f'predictions_{horizon}s.csv',[
                dict(time_ns=int(times[i]),label_end_ns=int(ends[i]),y=int(y[i]),**{k:float(v[i]) for k,v in probabilities.items()})
                for i in np.flatnonzero(test)])
        summary['horizons'][str(horizon)]=result
    for fig,ax,ylabel,path in [(qfig,qax,'Forward log return (bps)','quantile_return.png'),(pfig,pax,'P(mid increases), zero moves included','quantile_probability.png')]:
        ax.set(xlabel='OBI quantile (training cutoffs)',ylabel=ylabel,title='Full-session exploratory means | 30s block pointwise 95% CI')
        ax.legend();fig.tight_layout();fig.savefig(output/path,dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4))
    for name in ['baseline','obi','obi_spread_microprice']:
        xx=[];yy=[]
        for h in cfg['horizons_seconds']:
            model=summary['horizons'][str(h)]['models'].get(name)
            if model:xx.append(h);yy.append(model['test']['balanced_accuracy'])
        ax.plot(xx,yy,'o-',label=name)
    ax.axhline(.5,color='gray',linestyle='--');ax.legend()
    ax.set(xlabel='Clock-time horizon (seconds)',ylabel='Test balanced accuracy',title='Chronological 60/20/20 | zeros excluded | purged boundaries')
    fig.tight_layout();fig.savefig(output/'horizon_performance.png',dpi=160);plt.close(fig)
    write_csv(output/'model_metrics.csv',all_metrics)
    write_csv(output/'quantiles.csv',quantile_rows)
    # Verify frozen source files did not change during this run.
    for item,p in zip(inventory,files,strict=True):
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Source changed during run')
    dump(output/'input_manifest.json',dict(bbo_directory=str(folder),recorder_directory=str(evidence_dir.resolve()),files=inventory,evidence=evidence))
    summary['code_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src').glob('**/*.py'))+ [ROOT/'research/run.py',ROOT/'research/design.json']}
    dump(output/'summary.json',summary)
    import importlib.metadata as md
    dump(output/'environment.json',dict(python=sys.version,packages={k:md.version(k) for k in ['numpy','pyarrow','matplotlib','scikit-learn']}))
    print(json.dumps(dict(audit=audit,session=session,metrics=all_metrics),indent=2))


if __name__=='__main__':main()
