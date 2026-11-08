"""Render frozen external results only; no fitting or market-input reads."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/oos'
NAMES={'baseline':'Training majority','price_change':'Past-price rule','obi':'OBI','obi_spread_microprice':'OBI + spread + microprice'}
MODELS=list(NAMES)


def load(name):return json.loads((OUT/name).read_text())

def ci_text(ci):return f'[{ci[0]:.3f}, {ci[1]:.3f}]' if ci else 'undefined'

def score(value):return f'{value:.3f}' if value is not None else 'undefined'

def bounds(record,key):
    b=record['bootstrap'].get('60s_offset0')
    return b['ci95'].get(key) if b and b.get('ci95') else None


def row_model(h,record,m):
    x=record['models'][m]
    if x is None:return f'| {h}s | {NAMES[m]} | 0 | — | — | — | — |'
    return f"| {h}s | {NAMES[m]} | {x['n']} | {score(x['accuracy'])} {ci_text(bounds(record,m+'_accuracy'))} | {score(x['balanced_accuracy'])} {ci_text(bounds(record,m+'_balanced_accuracy'))} | {score(x['roc_auc'])} | `{x['confusion_matrix']}` |"


def graphs(first,robust,pilot):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':170})
    groups=[('First external',first['horizons'],'#222222','o')]+[(day,records,color,marker) for (day,records),color,marker in zip(robust['dates'].items(),['#3573a5','#b65a30'],['s','^'])]
    for key,ylabel,filename in [('mean_return_bps','Forward log return (bps)','quantile_return.png'),('probability_up','P(mid increases), zeros included','quantile_probability.png')]:
        fig,axes=plt.subplots(1,3,figsize=(12,3.8),sharex=True)
        for ax,h in zip(axes,['1','5','10']):
            for name,records,color,marker in groups:
                qs=records[h]['quantiles'];x=[q['quantile'] for q in qs];y=[q[key] for q in qs]
                ax.plot(x,y,marker=marker,color=color,label=name,linewidth=1.1,markersize=4)
                if name=='First external':
                    field='return_bps' if key=='mean_return_bps' else 'up_probability'
                    cis=[bounds(records[h],f'q{i}_{field}') for i in range(len(qs))]
                    for xx,c in zip(x,cis):
                        if c:ax.vlines(xx,c[0],c[1],color=color,linewidth=.8,alpha=.55)
            ax.set(title=f'{h}-second horizon',xlabel='Original-training OBI bin',xticks=range(1,6));ax.axhline(0,color='.8',linewidth=.7)
        axes[0].set_ylabel(ylabel);axes[0].legend(frameon=False,fontsize=8)
        fig.suptitle('Frozen training cutoffs | first-session 60s block pointwise intervals',fontsize=11)
        fig.tight_layout();fig.savefig(OUT/filename);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.5,4.2))
    original={h:pilot['horizons'][h]['models']['obi']['test']['balanced_accuracy'] for h in ['1','5','10']}
    ax.plot([1,5,10],list(original.values()),'o:',color='.5',label='Original pilot test (same-session)')
    for name,records,color,marker in groups:
        y=[records[h]['models']['obi']['balanced_accuracy'] for h in ['1','5','10']]
        ax.plot([1,5,10],y,marker=marker,color=color,label=name,linewidth=1.2)
        for x,h in zip([1,5,10],['1','5','10']):
            c=bounds(records[h],'obi_balanced_accuracy')
            if c:ax.vlines(x,c[0],c[1],color=color,linewidth=.8,alpha=.65)
    ax.axhline(.5,color='.6',linestyle='--',linewidth=.8)
    ax.set(xlabel='Receipt-clock horizon (seconds)',ylabel='Directional balanced accuracy',ylim=(.4,1),title='Frozen OBI | 60s pointwise block intervals')
    ax.legend(frameon=False,fontsize=8);fig.tight_layout();fig.savefig(OUT/'horizon_performance.png');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,9),sharey=True)
    sessions=robust['sessions'];labels=[f"S{i+1:02d} {s['dates'][0][5:]}"+(' *' if s['role']=='first_external' else '') for i,s in enumerate(sessions)]
    for ax,h in zip(axes,['1','5','10']):
        for m,offset,color,marker in [('price_change',-.14,'.6','x'),('obi',0,'#3573a5','o'),('obi_spread_microprice',.14,'#b65a30','+')]:
            for i,s in enumerate(sessions):
                record=s['horizons'][h];model=record['models'][m]
                if model and model['balanced_accuracy'] is not None:
                    ax.plot(model['balanced_accuracy'],i+offset,marker=marker,color=color,markersize=4)
                    c=bounds(record,'obi_balanced_accuracy') if m=='obi' else None
                    if c:ax.hlines(i,c[0],c[1],color=color,linewidth=.6,alpha=.5)
        ax.axvline(.5,color='.7',linestyle='--',linewidth=.8)
        ax.set(xlim=(0,1.02),title=f'{h}s',xlabel='Balanced accuracy')
    axes[0].set(yticks=range(len(labels)),yticklabels=labels);axes[0].invert_yaxis()
    fig.suptitle('All 25 forward-only sessions | blank = no two-class directional score\nBlue OBI; orange combined; gray past-price rule; * first external; 60s OBI intervals',fontsize=10)
    fig.tight_layout();fig.savefig(OUT/'session_performance.png');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4));centers=np.linspace(-.95,.95,20)
    for day,d in robust['feature_distributions'].items():ax.step(centers,np.array(d['histogram'])/d['n'],where='mid',label=f"{day} (n={d['n']:,})")
    ax.set(xlabel='L1 OBI',ylabel='Fraction of valid clock states',title='External-role dates | reserved and pilot sessions excluded');ax.legend(frameon=False)
    fig.tight_layout();fig.savefig(OUT/'daily_obi_distribution.png');plt.close(fig)


def main():
    first=load('first_external.json');r=load('chronological_robustness.json');pilot=json.loads((ROOT/'results/summary.json').read_text());inventory=load('inventory.json')
    graphs(first,r,pilot)
    rows=[]
    for s in r['sessions']+r.get('retrospective_diagnostic_sessions',[]):
        for h,d in s['horizons'].items():
            for m,x in d['models'].items():
                rows.append(dict(session_id=s['session_id'],dates=','.join(s['dates']),role=('pretraining_diagnostic_only' if s in r.get('retrospective_diagnostic_sessions',[]) else s['role']),horizon_seconds=h,model=m,labels=d['labels'],up=d['up'],down=d['down'],zero=d['zero'],n=x['n'] if x else 0,accuracy=x['accuracy'] if x else None,balanced_accuracy=x['balanced_accuracy'] if x else None,roc_auc=x['roc_auc'] if x else None,confusion_matrix=x['confusion_matrix'] if x else None,ba_ci60=bounds(d,m+'_balanced_accuracy')))
    with (OUT/'session_model_metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    date_rows=[]
    for day,records in r['dates'].items():
        for h,d in records.items():
            for m,x in d['models'].items():date_rows.append(dict(date=day,horizon_seconds=h,model=m,labels=d['labels'],directional=d['directional'],up=d['up'],down=d['down'],zero=d['zero'],**(x or {}),ba_ci60=bounds(d,m+'_balanced_accuracy')))
    with (OUT/'date_model_metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(date_rows[0]));w.writeheader();w.writerows(date_rows)
    lines=['# Frozen-model independent-session validation','',
'**Result:** the positive OBI relationship reproduced in the predesignated next-day session, with no external retraining or threshold selection. This is evidence from one new date, not multiple independent days. All numbers are conditional on the existing admission rules and (for classification) future nonzero returns.','',
'## Freeze and temporal separation','',
'[EXTERNAL_PROTOCOL.md](EXTERNAL_PROTOCOL.md) and `results/oos/protocol.json` were recorded before external predictions. Frozen coefficients/scalers/quantile edges are in `results/oos/frozen_models.json`. The original101/391/641 training observations recreate original test predictions before new evaluation. No external observation reaches fit(). The entire original session ended2026-10-07 07:44:11 UTC; the first external begins2026-10-08 01:56:14 UTC, with no timestamp or event-ID overlap. Its preceding selection used quality only. Local provenance records are not independent exchange signatures.','',
'External session `95a74716c1c140eb8e896cb11f924151`: 16,945 raw BBO,43.6minutes,2,616 one-second states,2,614 usable states. All eligible times are evaluated; there is no new internal train/test split. Original pilot test was only the final20% of its42-minute interval.','',
'| Horizon | Forward labels | Up | Down | Unchanged | Direction N | Original test N |','|---|---:|---:|---:|---:|---:|---:|']
    for h,d in first['horizons'].items():lines.append(f"| {h}s | {d['labels']:,} | {d['up']} ({d['up']/d['labels']:.1%}) | {d['down']} ({d['down']/d['labels']:.1%}) | {d['zero']} ({d['zero']/d['labels']:.1%}) | {d['directional']:,} | {pilot['horizons'][h]['models']['obi']['test']['n']} |")
    lines+=['','The1-second count rose from56 to438 partly because43.6minutes are evaluated rather than about8.5minutes, and partly because the nonzero rate is16.8% versus10.9% in the original test. Neither438 overlapping/state-dependent labels nor44 one-minute blocks represent438 independent market episodes. Zero exclusion is outcome-conditioned; these are not unconditional next-second trading scores.','',
'## All fixed models','',
'Entries show point estimate and60s paired clock-block pointwise95% CI. Confusion matrices: rows=true down/up; columns=predicted down/up. AUC has no CI here and is null without both classes.','',
'| Horizon | Model | N | Accuracy [CI] | Balanced Accuracy [CI] | AUC | Confusion matrix |','|---|---|---:|---|---|---:|---|']
    for h,d in first['horizons'].items():
        for m in MODELS:lines.append(row_model(h,d,m))
    lines+=['','| Horizon | OBI−majority Accuracy CI | OBI−price-rule Accuracy CI | OBI−majority BA CI | OBI−price-rule BA CI |','|---|---|---|---|---|']
    for h,d in first['horizons'].items():lines.append('| '+h+'s | '+' | '.join(ci_text(bounds(d,key)) for key in ['obi_minus_baseline_accuracy','obi_minus_price_change_accuracy','obi_minus_baseline_balanced_accuracy','obi_minus_price_change_balanced_accuracy'])+' |')
    lines+=['','These intervals favor OBI in this candidate under the registered block assumptions. They condition on the fitted original model and this session, omit between-day/training-estimation uncertainty, and do not establish universal superiority. Combined-feature performance is nearly identical or slightly worse; microprice is a deterministic OBI×spread interaction.','',
'## Returns, quantiles and horizon','',
'| Horizon | OBI/return correlation [60s CI] | Lowest/highest-bin mean return bps | Lowest/highest-bin P(up) | Nondecreasing bin means? |','|---|---|---|---|---|']
    for h,d in first['horizons'].items():
        lo,hi=d['quantiles'][0],d['quantiles'][-1]
        lines.append(f"| {h}s | {d['correlation']:.3f} {ci_text(bounds(d,'correlation'))} | {lo['mean_return_bps']:.3f} / {hi['mean_return_bps']:.3f} | {lo['probability_up']:.1%} / {hi['probability_up']:.1%} | {d['quantile_returns_nondecreasing']} |")
    lines+=['','All bin cutoffs come from original training, not the external distribution; bin counts need not be equal. Probabilities include unchanged returns. Direction-model BA decreases with horizon, while unconditional correlation rises from1s to5s and then falls at10s. A blanket statement that every predictive relationship decays monotonically is unsupported.','',
'![OBI quantile returns](../results/oos/quantile_return.png)','','![OBI quantile up probability](../results/oos/quantile_probability.png)','',
'## Block sensitivity','',
'44 one-minute blocks support each horizon (35/37/37 contain both directional classes). This is more than the original test9 blocks, but not independent dates. The following intervals report every registered length/alignment rather than selecting a favorable setting.','',
'| Horizon | Block / offset | Blocks | OBI BA CI | OBI−price BA CI |','|---|---|---:|---|---|']
    for h,d in first['horizons'].items():
        for key,b in d['bootstrap'].items():lines.append(f"| {h}s | {key} | {b['blocks']} | {ci_text(b['ci95']['obi_balanced_accuracy'])} | {ci_text(b['ci95']['obi_minus_price_change_balanced_accuracy'])} |")
    lines+=['',
'Full metrics, class coverage, bin counts and uncertainty diagnostics: [first_external.json](../results/oos/first_external.json). Per-observation prediction CSVs are local under ignored `data/`, not bundled raw data. Reproduction commands are in the README; the first external stage never calls fit(). The final reserved session remains unevaluated.']
    (ROOT/'research/INDEPENDENT_VALIDATION.md').write_text('\n'.join(lines)+'\n')
    robust_report(r,inventory)
    print('Rendered5 figures,2 CSV tables and2 result documents')


def robust_report(r,inventory):
    lines=['# Fixed-model date and session robustness','',
'The archive contains **two UTC dates, not28 independent trading days**. Oct7 includes the original training date; Oct8 is the only new date. All25 forward-only sessions plus1 pre-training diagnostic are disclosed. The latter was discovered in a post-protocol temporal-role audit; the registered26-session aggregate is preserved separately. The full original session(55,310 rows) and latest reserved session(77,143 rows) are excluded. No concatenation, cross-session labels, cross-date labels, interpolation, re-fit or favorable-session selection was performed. See [the transparent protocol addendum](EXTERNAL_PROTOCOL_ADDENDUM.md) for the chronological correction. First-external observations are included once in these broader date summaries, so those summaries are not additional independent replications of the first result.','',
'## Date-level results','',
'| UTC date | Horizon | Labels | Up / Down / Zero | Direction N | Majority BA | Price-rule BA | OBI BA [60s CI] | Combined BA | OBI/return correlation |','|---|---|---:|---|---:|---:|---:|---|---:|---:|']
    for day,records in r['dates'].items():
        for h,d in records.items():
            m=d['models'];lines.append(f"| {day} | {h}s | {d['labels']:,} | {d['up']:,} / {d['down']:,} / {d['zero']:,} | {d['directional']:,} | {score(m['baseline']['balanced_accuracy'])} | {score(m['price_change']['balanced_accuracy'])} | {score(m['obi']['balanced_accuracy'])} {ci_text(bounds(d,'obi_balanced_accuracy'))} | {score(m['obi_spread_microprice']['balanced_accuracy'])} | {score(d['correlation'])} |")
    lines+=['','Daily CIs resample clock blocks separately within each observed session-date and preserve session composition. They are **not** intervals for performance on a random new trading day. There is no date bootstrap: two dates, only one new date, are insufficient for a credible between-day distribution.','',
'![Horizon performance](../results/oos/horizon_performance.png)','','## OBI distributions','',
'| Date | Valid feature-grid states | OBI min / p10 / median / p90 / max |','|---|---:|---|']
    for day,d in r['feature_distributions'].items():lines.append(f"| {day} | {d['n']:,} | "+' / '.join(f'{v:.3f}' for v in d['quantiles'])+' |')
    lines+=['','![Daily OBI distributions](../results/oos/daily_obi_distribution.png)','','## Every forward-only session','',
'Blank/undefined BA means there are no two-class directional observations, not poor results removed from the report. Session IDs map directly to chronological S-labels in the figure. Short-session scores with both classes but very few labels are descriptive; CIs are null with fewer than4 time blocks.','',
'| S | Session ID | Date(s) | Raw rows | 1s direction N / BA | 5s direction N / BA | 10s direction N / BA |','|---|---|---|---:|---|---|---|']
    for i,s in enumerate(r['sessions']):
        vals=[]
        for h in ['1','5','10']:
            d=s['horizons'][h];m=d['models']['obi'];vals.append(f"{d['directional']} / {score(m['balanced_accuracy']) if m else 'undefined'}")
        lines.append(f"| S{i+1:02d} | `{s['session_id']}` | {', '.join(s['dates'])} | {s['raw_rows']:,} | "+' | '.join(vals)+' |')
    lines+=['','![Every-session performance](../results/oos/session_performance.png)','',
'The pre-training44-second session `f1d0c0b3bd1f4c7b844074508477be4c` is retained as a retrospective diagnostic only:1/5/10s directional N=7/17/22, OBI BA=1.000/0.694/0.637. It is excluded from the figures and date/pooled forward-only estimates; its rows remain in the metrics CSV with an explicit diagnostic role.','',
'All four models, Accuracy, BA, ROC-AUC, matrices, class counts and60s BA intervals appear in [session_model_metrics.csv](../results/oos/session_model_metrics.csv); date equivalents are in [date_model_metrics.csv](../results/oos/date_model_metrics.csv). The pooled result weights observations, whereas session/date tables expose heterogeneity. No equal-day generalization is inferred from the pooled number.','',
'## Pooled external-role evidence','',
'| Horizon | Labels | Direction N | OBI BA [60s CI] | OBI−majority BA CI | OBI−price BA CI | Correlation [60s CI] | Monotone quantile means? |','|---|---:|---:|---|---|---|---|---|']
    for h,d in r['pooled'].items():lines.append(f"| {h}s | {d['labels']:,} | {d['directional']:,} | {score(d['models']['obi']['balanced_accuracy'])} {ci_text(bounds(d,'obi_balanced_accuracy'))} | {ci_text(bounds(d,'obi_minus_baseline_balanced_accuracy'))} | {ci_text(bounds(d,'obi_minus_price_change_balanced_accuracy'))} | {score(d['correlation'])} {ci_text(bounds(d,'correlation'))} | {d['quantile_returns_nondecreasing']} |")
    lines+=['','Block lengths30/60/120s and half-block offsets are all recorded in robustness.json for pooled/date results. Their CIs remain conditional on fixed sessions and do not include training-estimation/model-selection/multiple-comparison uncertainty. Labels overlap for5s/10s; even1s non-overlapping returns can share persistent OBI/market regimes. Many clock blocks are more information than9 blocks, but not more independent trading dates.','',
'## Causal market-state diagnostics','',
'Low/high thresholds are the original training medians. Volatility is trailing60-second RMS past1-second log returns in bps, requiring60 valid increments; it is neither forward/realized target volatility nor an annualized estimate. Unknown windows are reported. No regime threshold was fitted on new outcomes. These strata differ in session/class composition and do not identify a causal regime effect.','',
'| Horizon | Variable | Fixed cutoff | Regime | Labels | Direction N | Price BA | OBI BA | Combined BA |','|---|---|---:|---|---:|---:|---:|---:|---:|']
    for h,fields in r['regimes'].items():
        for field,value in fields.items():
            for name,d in value['groups'].items():
                m=d['models'];format_m=lambda key:score(m[key]['balanced_accuracy']) if m[key] else 'undefined'
                lines.append(f"| {h}s | {field} | {value['training_median_threshold']:.6g} | {name} | {d['labels']:,} | {d['directional']:,} | {format_m('price_change')} | {format_m('obi')} | {format_m('obi_spread_microprice')} |")
    lines+=['','## Registered sampling/admission sensitivity','',
'Primary conditions remain receipt TTL2s and exchange-to-receipt lag[0,2]s on a1s grid. The diagnostics tighten TTL to1s, tighten lag to<=0.5s, or keep every other decision start while retaining exact1/5/10s endpoints from the1s price grid. They do not select a winning variant. Different retention changes the cohort, so score differences are not pure causal latency effects.','',
'| Condition | Horizon | Labels | Direction N | OBI BA | Price-rule BA |','|---|---|---:|---:|---:|---:|']
    for condition,records in [('primary',r['pooled'])]+list(r['sensitivity'].items()):
        for h,d in records.items():lines.append(f"| {condition} | {h}s | {d['labels']:,} | {d['directional']:,} | {score(d['models']['obi']['balanced_accuracy'])} | {score(d['models']['price_change']['balanced_accuracy'])} |")
    lines+=['','## Observed heterogeneity and limitations','',
'The next-day primary result is stronger than the original pilot, while date-level OBI BA differs by roughly0.0–1.4percentage points across the onlytwo available dates. That is not a confidence interval for new-date stability. Session-level dispersion is wider and tiny cohorts can yield1.0 BA; all are disclosed. Across evaluable forward-only sessions the point-score comparison favors OBI, but sessions are neither independent days nor equally informative.','',
'Causal past-volatility strata show lower OBI BA in the high-volatility group at all three horizons. This is a descriptive association, not proof that volatility causes predictability to decline. The original-training spread cutoff puts almost every new directional observation in the high group; the low group is too sparse for a meaningful spread-regime claim. The combined model provides no clear repeatable improvement. Lag-group differences are mixed across horizons. Tightening admission or halving decision frequency changes scores modestly, but also changes the admitted cohort and cannot identify a causal latency benefit.','',
'## Scope of inference','',
'- A positive OBI/forward-mid relationship and direction-model ranking are observed on the new date; numerical outcomes for every session are retained, including failures/undefined small samples.','- Direction BA generally decays over1→5→10s. Correlation and quantile mean-return magnitudes need not decay monotonically. Regime and date comparisons are descriptive and confounded by different admissible cohorts.','- Spread/microprice do not establish a repeatable incremental advantage; their mathematical dependence and original small training sample restrict interpretation.','- Negative exchange/receive differences invalidate67,059 archive rows; another6,036 exceed2s. This creates a clock/admission-selected sample. Clock differences are not pure measured network latency without trusted synchronization.','- Only one new date is tested. More ticks, sessions, blocks and narrow conditional CIs do not establish market-regime generalization. The latest session remains reserved; expanding to several independent dates is still needed.','- No executable profitability is established. Mid is not an execution price; spread/fees, queue position, latency, cancellation/fill probabilities and own-order impact can dominate sub-bps forecast returns. Queue/fill simulation, realized slippage and market impact were not measured.','',
'Full chronological record: [chronological_robustness.json](../results/oos/chronological_robustness.json). The original registered all-role record remains [robustness.json](../results/oos/robustness.json). Raw BBO and per-event predictions are not redistributed. No collection, original-repository edits, commit or push was performed.']
    (ROOT/'research/ROBUSTNESS.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
