"""Render final-v1 records/cache; raw inputs are read only for delay distribution.

No estimator fitting, rule selection, or changes to recorded Primary results.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/final_v1';DOC=ROOT/'research/final_v1'
spec=importlib.util.spec_from_file_location('final_analysis',DOC/'run.py');final=importlib.util.module_from_spec(spec);spec.loader.exec_module(final)
NAMES={'baseline':'Training up-prior','price_change':'Past1s price rule','obi':'OBI Logistic','obi_spread_microprice':'Combined Logistic'}


def read(p):return json.loads(Path(p).read_text())

def fmt(v):return 'undefined' if v is None else f'{v:.3f}'

def ci(v):return 'undefined' if not v else f'[{v[0]:.3f}, {v[1]:.3f}]'

def primary_ci(record,key):return record['bootstrap']['60s_offset0']['ci95'][key]


def plots(primary,extra,protocol,raw):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':170})
    rows={h:pq.read_table(final.PRIVATE/f'holdout_{h}s.parquet').to_pylist() for h in ['1','5','10']}
    title='Final consumed Holdout | 2026-10-08 15:15–17:15 UTC | all valid labels'
    fig,ax=plt.subplots(figsize=(7,4));ax.hist([r['obi'] for r in rows['1']],bins=np.linspace(-1,1,41),color='#3573a5')
    ax.set(xlabel='L1 OBI',ylabel='1s labeled observations',title=title+f"\nN={len(rows['1']):,}; zeros included")
    fig.tight_layout();fig.savefig(OUT/'obi_distribution.png');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,h in zip(axes,['1','5','10']):
        d=extra['holdout'][h];old=extra['seen_pooled'][h];x=np.arange(1,6)
        for name,r,color,style in [('Seen25 sessions',old,'.55','s--'),('Final Holdout',d,'#3573a5','o-')]:ax.plot(x,[r['point'][f'q{q}_ret'] for q in range(5)],style,color=color,label=name,markersize=4,linewidth=1)
        for q in range(5):
            c=d['uncertainty']['ci95'][f'q{q}_ret'];ax.vlines(q+1,c[0],c[1],color='#3573a5',linewidth=.8)
        ax.axhline(0,color='.8',linewidth=.7);ax.set(title=f"{h}s, N={d['n']:,}",xlabel='Original-training OBI bin',xticks=range(1,6))
    axes[0].set_ylabel('Mean forward log return (bps)');axes[0].legend(frameon=False,fontsize=8)
    fig.suptitle(title+'\n60s pointwise block intervals for Holdout',fontsize=10);fig.tight_layout();fig.savefig(OUT/'quantile_return.png');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
    for ax,h in zip(axes,['1','5','10']):
        d=extra['holdout'][h]
        for key,label,color in [('up','Up','#3573a5'),('down','Down','#b65a30'),('flat','Unchanged','.45')]:
            ax.plot(range(1,6),[d['point'][f'q{q}_{key}'] for q in range(5)],'o-',label=label,color=color,linewidth=1,markersize=3)
            for q in range(5):
                c=d['uncertainty']['ci95'][f'q{q}_{key}'];ax.vlines(q+1,c[0],c[1],color=color,linewidth=.6,alpha=.6)
        ax.set(title=f"{h}s, N={d['n']:,}",xlabel='Original-training OBI bin',xticks=range(1,6),ylim=(0,1))
    axes[0].set_ylabel('Unconditional outcome probability');axes[0].legend(frameon=False,fontsize=8)
    fig.suptitle(title+'\nUp + down + unchanged = 1; 60s pointwise intervals',fontsize=10);fig.tight_layout();fig.savefig(OUT/'direction_probability.png');plt.close(fig)
    first=read(ROOT/'results/oos/first_external.json');seen=read(ROOT/'results/oos/chronological_robustness.json')
    fig,axes=plt.subplots(1,2,figsize=(11.5,4))
    for label,r,color in [('First next-day session',first['horizons'],'.55'),('Seen25 pooled',seen['pooled'],'#b65a30'),('Final Holdout',primary['horizons'],'#3573a5')]:
        axes[0].plot([1,5,10],[r[h]['models']['obi']['balanced_accuracy'] for h in ['1','5','10']],'o-',color=color,label=label,linewidth=1)
    for x,h in zip([1,5,10],['1','5','10']):
        c=primary_ci(primary['horizons'][h],'obi_balanced_accuracy');axes[0].vlines(x,c[0],c[1],color='#3573a5')
    axes[0].axhline(.5,color='.7',linestyle='--',linewidth=.7);axes[0].set(title='A: conditional directional BA',ylabel='Balanced accuracy',ylim=(.3,1),xlabel='Horizon (seconds)');axes[0].legend(frameon=False,fontsize=8)
    for key,label,color in [('forced','Forced direction','#3573a5'),('gated','Fixed abstention band','#b65a30'),('flat_baseline','Training flat baseline','.5')]:
        axes[1].plot([1,5,10],[extra['holdout'][h]['three_action'][key]['accuracy'] for h in ['1','5','10']],'o-',label=label,color=color,linewidth=1)
    axes[1].set(title='B: all-label three-action agreement',ylabel='Agreement, not economic return',ylim=(0,1),xlabel='Horizon (seconds)');axes[1].legend(frameon=False,fontsize=8)
    fig.suptitle('2026-10-08 final2h | A nonzero N1/5/10s=4184/6464/6760\nB all-label N1/5/10s=7034/7010/6980; different estimands and denominators',fontsize=9)
    fig.tight_layout();fig.savefig(OUT/'horizon_performance.png');plt.close(fig)
    sessions=seen['sessions']+[dict(session_id=final.HOLDOUT,horizons=primary['horizons'])]
    fig,axes=plt.subplots(1,3,figsize=(13,9),sharey=True)
    labels=[]
    for i,s in enumerate(sessions):
        ns=[s['horizons'][h]['directional'] for h in ['1','5','10']]
        labels.append(('FINAL' if i==len(sessions)-1 else f'S{i+1:02d}')+' '+ '/'.join(map(str,ns)))
    for ax,h in zip(axes,['1','5','10']):
        for i,s in enumerate(sessions):
            r=s['horizons'][h];m=r['models']['obi']
            if m and m['balanced_accuracy'] is not None:
                color='#b65a30' if i==len(sessions)-1 else '#3573a5';ax.plot(m['balanced_accuracy'],i,'o',color=color,markersize=3)
                b=r['bootstrap'].get('60s_offset0');c=b['ci95'].get('obi_balanced_accuracy') if b and b.get('ci95') else None
                if c:ax.hlines(i,c[0],c[1],color=color,linewidth=.7,alpha=.6)
        ax.axvline(.5,color='.7',linestyle='--',linewidth=.7);ax.set(xlim=(.3,1.02),title=f'{h}s',xlabel='Conditional BA')
    axes[0].set(yticks=range(len(labels)),yticklabels=labels);axes[0].tick_params(axis='y',labelsize=8);axes[0].invert_yaxis()
    fig.suptitle('2026-10-07/08 | 25 seen sessions + final interval\nLabels show N1s/N5s/N10s; blank = BA undefined; 60s conditional block intervals',fontsize=10)
    fig.tight_layout();fig.savefig(OUT/'session_performance.png');plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(12,7))
    for column,h in enumerate(['1','5','10']):
        d=extra['holdout'][h];lookup=protocol['training_only_magnitude_lookup'][h];q=np.arange(1,6)
        spread=[d['point'][f'q{i}_spread'] for i in range(5)];forecast=np.abs(lookup['bin_means_bps'])
        axes[0,column].bar(q-.15,forecast,width=.3,label='Abs training-bin forecast',color='#3573a5')
        axes[0,column].bar(q+.15,spread,width=.3,label='Current full quoted gap',color='.65')
        aligned=[np.sign(lookup['bin_means_bps'][i])*d['point'][f'q{i}_ret'] for i in range(5)]
        axes[1,column].bar(q-.15,aligned,width=.3,label='Ex post aligned mid change',color='#b65a30')
        axes[1,column].bar(q+.15,spread,width=.3,label='Current full quoted gap',color='.65')
        for row in range(2):axes[row,column].set(xticks=q,xlabel='OBI bin',title=f"{h}s, N={d['n']:,}");axes[row,column].axhline(0,color='.8',linewidth=.6)
    axes[0,0].set_ylabel('Ex ante magnitude / gap (bps)');axes[1,0].set_ylabel('Ex post markout / gap (bps)')
    axes[0,0].legend(frameon=False,fontsize=8);axes[1,0].legend(frameon=False,fontsize=8)
    fig.suptitle('Final Holdout | zeros included | training-only lookup is NOT Logistic magnitude\nEx post mid changes are not fills, realized costs or PnL',fontsize=10)
    fig.tight_layout();fig.savefig(OUT/'forecast_vs_spread.png');plt.close(fig)
    lag=np.array([(r['ingested_at']-r['timestamp'])/final.NS for r in raw]);admitted=np.array([r['lag_seconds'] for r in rows['1']])
    fig,axes=plt.subplots(1,2,figsize=(11.5,4))
    for values,label,color in [(lag,f'Raw BBO N={len(lag):,}', '.55'),(admitted,f'Valid1s labels N={len(admitted):,}','#3573a5')]:
        axes[0].hist(values,bins=np.linspace(0,1,41),weights=np.ones(len(values))/len(values),histtype='step',label=label,color=color)
        axes[1].plot(np.sort(values),np.arange(1,len(values)+1)/len(values),label=label,color=color,linewidth=1)
    axes[0].set(xlabel='Exchange-to-receive difference (s)',ylabel='Fraction per25ms bin',title=f'0–1s detail; raw >1s: {(lag>1).mean():.1%}');axes[0].legend(frameon=False,fontsize=8)
    for h in [1,5,10]:axes[1].axvline(h,color='.7',linestyle=':',linewidth=.8)
    axes[1].set(xlabel='Clock difference (s); dotted1/5/10s horizons',ylabel='Empirical CDF',xlim=(0,10),title=f'Full raw tail max={lag.max():.2f}s')
    fig.suptitle('Final interval 2026-10-08 15:15–17:15 UTC | observed clock difference, not certified network latency',fontsize=10)
    fig.tight_layout();fig.savefig(OUT/'delay_distribution.png');plt.close(fig)
    return dict(raw_delay_quantiles_seconds=np.quantile(lag,[0,.5,.95,1]).tolist(),raw_rows=len(raw),raw_lag_over1s=int((lag>1).sum()),raw_lag_over2s=int((lag>2).sum()))


def render(primary,e,p,delay):
    first=read(ROOT/'results/oos/first_external.json');seen=read(ROOT/'results/oos/chronological_robustness.json');old=read(ROOT/'results/summary.json')
    lines=['# Order Book Imbalance and Short-Horizon Price Predictability in BTC Markets','',
'Final-v1 research report. BTC perpetual L1 BBO; Hyperliquid local observed archive; protocol recorded before final disclosure. All times UTC. Primary A and exploratory B are explicitly separate.','',
'## 1. Abstract','',
'We study whether best-level order-book imbalance(OBI) predicts1/5/10-second BTC mid-price movements using682,024 observed BBO updates across28 sessions but onlytwo UTC dates. Original-training Logistic models are frozen before scoring a final77,143-update interval. Conditional-on-move Balanced Accuracy declines to0.764/0.625/0.577 from0.909/0.800/0.726 in the earlier next-day session, while remaining above fixed baselines under within-session block uncertainty. Including unchanged outcomes yields different coverage and action-agreement results, and the conditional score is not an unconditional probability. Training-only OBI-bin expected moves and quoted-gap comparisons do not establish executable profitability; a predeclared1-second deferred markout sensitivity further weakens direction discrimination. The final interval is now consumed, and the two-date archive cannot support broad independent-day generalization.','',
'## 2. Introduction','',
'Displayed liquidity can contain short-horizon information, yet a directional relationship is not equivalent to a deployable trading rule. This compact study reuses Liquidation Gravity\'s existing quote metric, avoids new collection/execution infrastructure, and emphasizes available-at-decision information, fixed estimation, temporal validation and honest market-state dependence. BBO provides prices and displayed sizes at the best levels, not individual orders or fills. This report distinguishes predictable quote revisions from achievable net trading returns.','',
'## 3. Research Hypothesis','',
'A asks whether OBI predicts sign(r) given r!=0. Its primary endpoint is1s frozen OBI Balanced Accuracy and paired gain against the original training-majority baseline; other horizons/models are secondary. B asks whether OBI contains useful information over **all** admissible observation times, including r=0. B is assessed through unconditional bin means/outcome probabilities, score ranking, coverage and fixed-action diagnostics. It is not substituted for A.','',
'Formally, `p_A(x)=P(r>0 | r!=0,x)`, whereas `P(r>0 | x)=P(r!=0 | x) p_A(x)`. The original binary model does not estimate the first factor. A high conditional accuracy therefore neither identifies when a price will move nor supplies a calibrated all-time probability. A constant-flat classifier can have high raw agreement in a quiet market without contradicting positive OBI information in conditional means.','',
'## 4. Dataset and Data Quality','',
'The existing archive contains682,024 BBO across28 session IDs on2026-10-07/08, not28 independent days. One session crosses midnight. Numeric bid/ask prices and sizes are complete and positive, with no crossed quotes, but67,059 rows have negative exchange–receive differences and6,036 exceed2s. The earlier audit found5 adjacent exchange timestamp reversals. These clock differences are not corrected to gain samples. Sessions are not joined or interpolated.','',
'The original42-minute pilot uses15,295 quotes. Its entire55,310-row session is excluded from chronological external aggregates; a325-row pre-training interval is preserved as retrospective only. The25 prior chronological sessions contain549,246 quotes. Final validation uses the last77,143 quotes,2026-10-08 15:15:56.594595–17:15:56.455088 UTC. It is later in time but on the **same already observed Oct8 date**, not a third day. Prior final-source/quality inspection did not inspect returns or model scores.','',
'Final quality:7,200 clock states,7,041 valid states(97.79% feature coverage),1,841 raw clock differences>2s and no receive gaps>2s. Invalid-lag observations, rather than long receive gaps alone, can make a grid state unavailable. Independent UTC/monotonic clock evidence and loss-free feed coverage are not established. Raw redistribution rights and an exact public historical-download URL were not verified, so raw/event-level predictions remain unbundled.','',
'## 5. Feature Construction','',
'For best bid b, ask a and displayed quantities qb,qa: `mid=(b+a)/2`, `spread=a-b`, `relative_spread=spread/mid`, `OBI=(qb-qa)/(qb+qa)`, and `microprice=(a*qb+b*qa)/(qb+qa)`. Spread and microprice offsets are expressed in basis points. The identity `microprice_offset_bps=OBI*spread_bps/2` makes the added feature an interaction of the same L1 inputs, not independent data. Liquidation exposure, trade volume and synthetic OMS orders are not used.','',
'At clock time t, the feature uses the latest BBO with receive time<=t. Both sizes must be>0, prices finite and0<b<=a, exchange-to-receive difference in[0,2]s, and receipt age<=2s. Invalid latest states do not revive older valid quotes. Forward return is `r(t,h)=log(M(t+h)/M(t))`, using the same receive-as-of rule at the exact endpoint. Every grid state through the label path must be valid, and labels cannot cross sessions or UTC dates. Clock-time seconds are not event counts.','',
'## 6. Experimental Design','',
'Original60/20/20 elapsed-time splits use strict purging: training label endpoints precede validation, and validation endpoints precede test. Training nonzero counts are101/391/641 at1/5/10s. The saved training-only scalers, coefficients and feature order reproduce original predictions and remain unchanged(C=1,lbfgs,max_iter2000,threshold0.5). Baselines are a constant original-training up prior and the sign of the previous1s return, with zero/missing history falling back to that prior. No Holdout fitting or selection occurs; runtime fit calls are disabled.','',
'[Final protocol](PROTOCOL.md) records Primary A, exploratory rules, model/source fingerprints and training-only magnitude lookup before disclosure. The consumption ledger is written before labeling, and the resulting score is permanently seen. Replay checks the same calculation; it cannot restore an unused test. The earlier temporal-role correction is disclosed separately and original result files remain unchanged.','',
'Primary uncertainty uses paired nonoverlapping30/60/120-second clock blocks and origin/half-block alignment,1,000 replicates;60s intervals are displayed. Empty blocks remain, blocks do not bridge session/date boundaries, and models are compared on identical rows. These are pointwise intervals conditional on fixed models and the observed session composition; no date bootstrap, training-estimation uncertainty, or multiplicity-adjusted generalization claim is made.','',
'Exploratory B uses forced direction(p>=0.5), a fixed action band(up if p>0.6,down if p<0.4,else abstain), and the all-label original-training majority class(flat at each horizon). Coding abstention as0 permits descriptive three-action agreement/macro recall; it is not a fitted flat-price probability or economic utility. All-time up-vs-not-up AUC uses p only as a rank score, not calibrated probability. Five training-only bin means estimate magnitude separately from Logistic.','',
'## 7. Predictive Performance','',
'### Primary A: original target, final interval','',
'| h | Valid labels | Up / down / unchanged | Nonzero fraction | Label coverage |','|---|---:|---|---:|---:|']
    for h,d in primary['horizons'].items():lines.append(f"| {h}s | {d['labels']:,} | {d['up']:,} / {d['down']:,} / {d['zero']:,} | {d['directional']/d['labels']:.1%} | {d['coverage']['label_coverage']:.1%} |")
    lines+=['','Label coverage uses possible in-session grid pairs; the nonzero fraction is retrospective outcome coverage. It is not a deployable trigger.','',
'| h | Frozen model | Direction N | Accuracy | Balanced Accuracy [60s95% CI] | AUC(point) | Confusion matrix |','|---|---|---:|---:|---|---:|---|']
    for h,d in primary['horizons'].items():
        for name,m in d['models'].items():lines.append(f"| {h}s | {NAMES[name]} | {m['n']:,} | {m['accuracy']:.3f} | {m['balanced_accuracy']:.3f} {ci(primary_ci(d,name+'_balanced_accuracy'))} | {m['roc_auc']:.3f} | `{m['confusion_matrix']}` |")
    lines+=['','Matrices have rows=true down/up and columns=predicted down/up. Constant training majority remains upward even though final nonzero observations are slightly downward-skewed; it is not reselected using test labels.','',
'| h | OBI−majority Accuracy CI | OBI−price-rule Accuracy CI | OBI−price-rule BA CI |','|---|---|---|---|']
    for h,d in primary['horizons'].items():lines.append('| '+h+'s | '+' | '.join(ci(primary_ci(d,k)) for k in ['obi_minus_baseline_accuracy','obi_minus_price_change_accuracy','obi_minus_price_change_balanced_accuracy'])+' |')
    lines+=['','| h | OBI BA CI,30s | 60s | 120s | 60s shifted30s |','|---|---|---|---|---|']
    for h,d in primary['horizons'].items():
        lines.append('| '+h+'s | '+' | '.join(ci(d['bootstrap'][key]['ci95']['obi_balanced_accuracy']) for key in ['30s_offset0','60s_offset0','120s_offset0','60s_offset30'])+' |')
    lines+=['','The final interval supports positive conditional discrimination under these block assumptions, but performance is materially lower than the first external session. Added spread/microprice barely change classifications and do not improve ranking consistently.','',
'### Exploratory B: all outcomes and coverage','',
'| h | All-label N | Forced agreement / macro recall | Fixed-band agreement / macro recall | Flat baseline agreement | Past-price forced agreement | Action coverage(features / labels) | Up-vs-not-up rank AUC |','|---|---:|---|---|---:|---:|---|---:|']
    for h,d in e['holdout'].items():
        a=d['three_action'];c=e['feature_coverage'][h]
        lines.append(f"| {h}s | {d['n']:,} | {a['forced']['accuracy']:.3f} / {a['forced']['balanced_accuracy']:.3f} | {a['gated']['accuracy']:.3f} / {a['gated']['balanced_accuracy']:.3f} | {a['flat_baseline']['accuracy']:.3f} | {d['model_all_time']['price_change']['all_time_forced']['accuracy']:.3f} | {c['policy_coverage_on_valid_features']:.1%} / {c['policy_coverage_on_valid_labels']:.1%} | {d['model_all_time']['obi']['up_vs_not_up_rank_auc']:.3f} |")
    lines+=['','These are different targets from A. At1s,0.767 conditional Accuracy becomes0.456 forced three-action agreement once2,850 unchanged outcomes are included. The fixed action band is active at roughly94% of valid feature times and does not learn a move detector. The training-flat baseline has0.405 agreement in the final interval but0.812 in the previously seen1s pool; accuracy alone depends strongly on the flat rate. B\'s per-policy matrices, block intervals and all original models\' forced-direction diagnostics are in exploration.json. For forced direction, all-time agreement equals nonzero_fraction × conditional Accuracy, and fixed3-class macro recall equals (2/3) × conditional BA because flat recall is zero. Those derived metrics are denominator diagnostics, not independent evidence of a learned move detector.','',
'![OBI distribution](../../results/final_v1/obi_distribution.png)','','![Horizon performance](../../results/final_v1/horizon_performance.png)','',
'## 8. Out-of-Sample Validation','',
'| h | Original same-session test BA(N) | First next-day BA(N) | Seen25 pooled BA(N) | Final BA(N) |','|---|---|---|---|---|']
    for h,d in primary['horizons'].items():
        a=old['horizons'][h]['models']['obi']['test'];b=first['horizons'][h]['models']['obi'];c=seen['pooled'][h]['models']['obi'];m=d['models']['obi']
        lines.append(f"| {h}s | {a['balanced_accuracy']:.3f}({a['n']}) | {b['balanced_accuracy']:.3f}({b['n']}) | {c['balanced_accuracy']:.3f}({c['n']}) | {m['balanced_accuracy']:.3f}({m['n']}) |")
    lines+=['','The original1s56 observations came from512 valid test labels minus456 zeros. Final4,184 moves arise from7,034 labels over nearly2hours with a59.5% nonzero rate; the earlier first external had438 moves and16.8% nonzero rate. Larger N reflects longer coverage and a different market state, not automatic independence or adequate new-day power. The last interval is a new temporal holdout of the same Oct8 calendar day. It is now consumed and cannot be used again as unused data after model redesign.','',
'## 9. Robustness Analysis','',
'Unconditional OBI-bin means rise at1s and5s in the final interval, while the10s middle bins are not monotone. Thus the positive extreme-bin spread is stronger evidence than an assertion of universal monotonicity or a specific nonlinear law. Binning is a nonparametric shape diagnostic, not a formal rejection of linearity. The fixed standardized OBI Logistic coefficients are retained in the model JSON; they are not re-estimated for new regimes.','',
'| h | Final lowest/highest-bin mean bps | Top−bottom60s CI | Lowest/highest P(up) | Lowest/highest P(down) |','|---|---|---|---|---|']
    for h,d in e['holdout'].items():
        a=d['point'];c=d['uncertainty']['ci95']['top_minus_bottom_return_bps']
        lines.append(f"| {h}s | {a['q0_ret']:.3f} / {a['q4_ret']:.3f} | {ci(c)} | {a['q0_up']:.1%} / {a['q4_up']:.1%} | {a['q0_down']:.1%} / {a['q4_down']:.1%} |")
    lines+=['','Probabilities include unchanged returns; bin cutoffs remain original training cutoffs and counts are unequal. Multiple bins/horizons/strata are exploratory.','',
'![OBI bins and return](../../results/final_v1/quantile_return.png)','','![OBI bins and all direction probabilities](../../results/final_v1/direction_probability.png)','',
'| Previously seen date | h | All labels | Nonzero fraction | Forced agreement | Flat agreement |','|---|---|---:|---:|---:|---:|']
    for day,hs in e['seen_dates'].items():
        for h,d in hs.items():lines.append(f"| {day} | {h}s | {d['n']:,} | {d['nonzero_fraction']:.1%} | {d['three_action']['forced']['accuracy']:.3f} | {d['three_action']['flat_baseline']['accuracy']:.3f} |")
    lines+=['','The two prior dates look similar in aggregate but the later final period differs substantially. Within-date heterogeneity therefore matters. Sparse/one-class sessions remain disclosed; previous source audits found no overlapping session ranges or duplicate events. Short-session sensitivity retains11 previously seen sessions with>=100 nonzero1s labels. It does not select sessions by Accuracy. All-time signed markouts and block intervals are supplied for this fixed subset alongside the full pool, and conditional confusion-matrix aggregation is in summary_tables.json.','',
'Past-volatility strata use original-training medians and trailing60s RMS past1s returns, requiring60 valid increments. Relative-spread/absolute-spread strata also use training thresholds. The older relative-spread low group is very sparse and cannot support a firm regime conclusion. New absolute-spread summaries are descriptive, with sample/class composition disclosed. No independent effect of spread or volatility on predictability is identified.','',
'![Every session and final interval](../../results/final_v1/session_performance.png)','',
'## 10. Execution Feasibility','',
'### Quoted spread and magnitude','',
'The original binary Logistic does not forecast magnitude. The separate exploratory forecast is `mu_hat(q,h)=mean_train[r_bps | original OBI bin=q]`, including zeros and estimated before final disclosure. It is compared with the current full quoted gap. A one-way crossing relative to mid is roughly half a gap; using a full instantaneous gap approximates two symmetric crossings only if spreads and executable quotes were unchanged. Actual entry/exit quotes, fees and fills are not simulated.','',
'| h | Mean abs training-bin forecast bps | Mean current gap bps | Forecast>gap | Forecast>gap+1bps | Forecast>gap+5bps | Ex post abs move>gap |','|---|---:|---:|---:|---:|---:|---:|']
    for h,d in e['holdout'].items():
        a=d['point'];lines.append(f"| {h}s | {a['forecast_abs']:.3f} | {a['spread']:.3f} | {a['forecast_exceeds_spread']:.1%} | {a['forecast_exceeds_spread_plus1']:.1%} | {a['forecast_exceeds_spread_plus5']:.1%} | {a['realized_abs_exceeds_spread']:.1%} |")
    lines+=['','Extreme OBI bins have larger mean gaps than middle bins in this final interval, but this is not an identified causal liquidity effect. The training lookup materially understates the observed extreme-bin markout magnitudes, indicating weak cross-state magnitude calibration; it is not revised using final returns. The1bps/5bps additions are assumed total round-trip cost scenarios, not measured Hyperliquid fees. No1s forecast exceeds the quoted gap; some5/10s forecasts do, but none exceed gap+1bps under this small original-training lookup. Ex post large moves cannot be selected in advance and do not establish capturable returns. The conditional forecast means change across periods and the tiny original training sample limits magnitude calibration.','',
'![Forecasts and quoted gap](../../results/final_v1/forecast_vs_spread.png)','',
'### Observation difference and conservative deferral','',
'Final raw exchange-to-receive differences(min/median/p95/max) are '+ '/'.join(f'{x:.3f}' for x in delay['raw_delay_quantiles_seconds'])+' seconds. These may reflect transport/processing, host/exchange clock mismatch and batching; the components are not separately identified, so the differences are not certified network/order-entry latency. Admitted1s labeled quotes have median0.306s andp950.639s, substantial relative to a1s horizon. Relative scales matter even though a temporal association remains.','',
'The predeclared conservative sensitivity keeps the decision feature fixed at t but evaluates `log(M(t+1+h)/M(t+1))`, requires both benchmark source receive/exchange times>t and a valid complete path. This excludes the first second of the original markout and changes label availability. It is a deferred observable-mid benchmark, not an execution price, fill model or measured order submission delay.','',
'| h | Primary labels / BA | Deferred labels / nonzero N | Deferred OBI BA [60s CI] |','|---|---|---|---|']
    for h,d in e['delayed'].items():
        old_h=primary['horizons'][h];m=d['conditional'];lines.append(f"| {h}s | {old_h['labels']:,} / {old_h['models']['obi']['balanced_accuracy']:.3f} | {d['delayed_labels']:,} / {m['directional']:,} | {m['models']['obi']['balanced_accuracy']:.3f} {ci(primary_ci(m,'obi_balanced_accuracy'))} |")
    lines+=['','![Observed clock differences](../../results/final_v1/delay_distribution.png)','',
'### What is not measured','',
'No actual order submission delay, realized slippage, queue position, own-order market impact, fill probability, cancellation exposure, unfilled-order opportunity cost or paid trading fees is observed. BBO sizes cannot reconstruct individual queues or identify the response to our own order. Spread comparisons and signed mid markouts are therefore diagnostic envelopes, **not a backtest, net PnL or realized transaction-cost estimate**.','',
'## 11. Limitations','',
'There are onlytwo archived dates and one date beyond training; the final interval is not another independent day. Many correlated states and narrow conditional block intervals do not supply a between-day distribution. Overlapping5/10s labels, persistent OBI, clock-based exclusions, invalid-path censoring, unobserved feed loss, class imbalance and source selection limit conclusions. Our block lengths are sensitivity settings, not certified independence lengths. Pointwise intervals are not multiple-testing-adjusted and do not include small-training-sample parameter or magnitude-lookup uncertainty.','',
'A evaluates an outcome-conditioned subset unknown at prediction time. B changes the denominator and action interpretation and is explicitly exploratory despite being fixed before final disclosure. The flat baseline is frozen from training and can be poor during an active market; it is not a live move model. Confidence-based abstention does not solve that missing model. The source has local collector/payload lineage but no independent exchange-authenticity or UTC attestation. Exact replay requires restricted inputs; code/aggregate evidence alone cannot regenerate historical prices.','',
'## 12. Conclusion','',
'OBI contains positive short-horizon information in this BTC BBO archive, including a final later interval, but the final conditional direction scores degrade materially and10s bin means are not universally monotone. The all-time analysis demonstrates that directional discrimination, event coverage, unconditional probabilities and decision utility are distinct. Forecast/spread comparisons and the deferral sensitivity expose a gap between quote predictability and executable profit. The reproducible result is a scoped empirical relationship with transparent failures and limits, not a deployable strategy or cross-regime alpha claim. Future redesign must use genuinely new dates and cannot reuse this consumed Holdout as unused validation.','',
'Reproduction: see [README](../../README.md), [protocol](PROTOCOL.md), [verification](VERIFICATION.md) and [Korean summary](SUMMARY_KO.md). Numerical evaluation/protocol/model artifacts remain unchanged. The public release omits private row files and redacts machine-specific metadata; see [publication scope](../../PUBLICATION.md).']
    (DOC/'REPORT.md').write_text('\n'.join(lines)+'\n')


def main(root):
    bundle,p=final.checked();primary=read(OUT/'primary_holdout.json');e=read(OUT/'exploration.json');manifest=final.oos.checked_inputs(root)
    raw=final.session_rows(root,manifest,final.HOLDOUT);delay=plots(primary,e,p,raw);final.save(OUT/'delay_summary.json',delay)
    render(primary,e,p,delay)
    # Conditional small-session sensitivity from immutable prior confusion matrices.
    seen=read(ROOT/'results/oos/chronological_robustness.json');keep=[s for s in seen['sessions'] if s['horizons']['1']['directional']>=100]
    summary={'large_session_count':len(keep),'conditional_large_session_metrics':{}}
    for h in ['1','5','10']:
        summary['conditional_large_session_metrics'][h]={}
        for name in NAMES:
            cm=sum((np.array(s['horizons'][h]['models'][name]['confusion_matrix']) for s in keep),np.zeros((2,2),dtype=int))
            summary['conditional_large_session_metrics'][h][name]=dict(n=int(cm.sum()),accuracy=float(np.trace(cm)/cm.sum()),balanced_accuracy=float(np.mean(np.diag(cm)/cm.sum(axis=1))),confusion_matrix=cm.tolist())
    final.save(OUT/'summary_tables.json',summary);final.checked();final.oos.checked_inputs(root)
    print('Rendered7 figures and12-section English report without changing Primary or old outputs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bbo-root',type=Path,required=True);main(parser.parse_args().bbo_root)
