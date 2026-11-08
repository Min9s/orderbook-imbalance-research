# Order Book Imbalance & Short-Horizon Mid-Price Prediction

A compact empirical market-microstructure study using existing Hyperliquid BTC perpetual BBO data and a reused Liquidation Gravity feature function. **The positive OBI relationship reproduced in one next-day session with frozen models. The archive has only two UTC dates, so broad market generalization remains untested.** No execution engine, collector, deep learning or trading-profit claim.

## 1. Research Question

**Does Order Book Imbalance predict short-term mid-price movements?**

The study separates the original42-minute pilot, a locally recorded pre-evaluation protocol, a next-day frozen-model validation, and broader chronological session diagnostics. It reports unchanged prices and undefined short-session scores rather than selecting successful periods.

## 2. Data Source and Actual Coverage

Observed **Hyperliquid mainnet BTC perpetual L1 BBO**, with both displayed prices/sizes, exchange timestamp, local receive timestamp, session ID and raw payload. These are not liquidation positions, trade volume or synthetic OMS orders. The original quote formula is extracted unchanged into `src/obi_research/legacy_book.py`; the analysis does not import either original project.

| Data role | Raw BBO | Use |
|---|---:|---|
| Full archive,2026-10-07/08 UTC | 682,024 | Quality inventory:28 sessions, **2 dates** |
| Original pilot subset,Oct7 05:17–05:59 UTC | 15,295 | Original chronological60/20/20 fit/validation/test |
| Entire original session | 55,310 | Excluded from all external aggregates, including its continuation |
| First next-day session,Oct8 01:56–02:39 UTC | 16,945 | Frozen-model external validation |
| All forward-only evaluation sessions | 549,246 | 25 sessions, includes first external once |
| Pre-training44-second diagnostic | 325 | Retrospective only; excluded from chronological results |
| Latest session,Oct8 15:15–17:15 UTC | 77,143 | Reserved final: quality inspected, **no labels or scores** |

The archive spans Oct7 05:14:56 to Oct8 17:15:56 UTC with observation gaps; it is not a continuous36-hour feed. One session crosses midnight, so daily session appearances sum to29 but there are28 IDs. All numeric quote fields are complete/positive/noncrossed; **67,059 rows have negative exchange–receive differences,6,036 exceed2s**, and5 adjacent exchange-time reversals occur. These clocks are not repaired to gain sample size. Existing admission produces82,570 valid1-second states across the entire archive;66,679 belong to the25 forward-only sessions.

[Full inventory and every session](research/EXTERNAL_INVENTORY.md) · [data access, rights review and collection plan](research/DATA_ACCESS.md).

Raw data and per-observation predictions are not redistributed: an applicable raw-data redistribution grant and an exact public historical-download URL were not established. Public access documentation is not a redistribution license. A public clone can test calculations and inspect aggregate evidence, but exact historical replay requires the original inputs. A new public BBO subscription reproduces the method, not these prices.

## 3. Features and Timing

| Feature | Definition |
|---|---|
| Mid | `(best_bid + best_ask)/2` |
| Spread / relative spread | `ask − bid` / `spread / mid` |
| L1 OBI | `(bid_size − ask_size)/(bid_size + ask_size)` |
| Microprice | `(ask×bid_size + bid×ask_size)/(bid_size + ask_size)` |

OBI measures relative displayed support. Positive OBI tilts microprice toward the ask; displayed orders may cancel. `microprice_offset_bps = OBI × spread_bps / 2`, so this is a deterministic interaction, not an independent source of information.

For each1-second receipt-clock time t, use the last BBO received<=t. Require finite positive prices and both sizes>0, bid<=ask, receipt age<=2s, exchange→receipt difference in[0,2]s, and no invalid intermediate grid state. `r(t,h)=log(mid(t+h)/mid(t))` uses the same as-of rule at the exact1/5/10-second endpoint; it never takes a quote received after that endpoint. No labels cross session or UTC-date boundaries. No interpolation or backward filling is used.

These are **clock seconds, not BBO-event counts**. The original median exchange→receive difference was261ms and feature exchange-age reached2.120s. Without trusted clock alignment this is neither pure measured network latency nor exchange-clock prediction. The [timing audit](research/STATISTICAL_AUDIT.md) covers actual code locations and staleness checks.

## 4. Frozen Research Design

[Protocol](research/EXTERNAL_PROTOCOL.md) · [immutable JSON protocol](results/oos/protocol.json) · [frozen coefficient/scaler bundle](results/oos/frozen_models.json).

- Original training only:60/20/20 by elapsed time, strict purging at validation/test boundaries. Nonzero training counts101/391/641 at1/5/10s. No external observation reaches fit(). Original test predictions were reproduced before external scores.
- Models: training-up-rate constant baseline; sign of past1-second return (zero/missing→training majority); Logistic on OBI; Logistic on OBI+spread_bps+microprice_offset_bps. C=1,lbfgs,max_iter2000,threshold0.5. Scaling and quantile cutoffs use original training only.
- Training scores are in-sample; original validation/test are later observations in the same session. The first external is a disjoint next-day session. Oct7 later sessions are chronological same-date diagnostics, **not new trading days**. Oct8 aggregates contain the first external, not another independent replication.
- Zero returns remain in statistical means/up probabilities and class-coverage counts, but are excluded from binary classification. Directional accuracy is conditional on a future move; this subset is unknown at decision time.
- Primary endpoint: first-external1s OBI Balanced Accuracy and paired gain over training-majority baseline. All other horizons/models/strata are secondary. No performance-driven retuning.
- Pointwise clock-block bootstrap:1,000 paired replicates,60s primary,30/120s and half-block alignment sensitivity. Blocks stay within session-date units and retain empty periods. No date bootstrap from just2 dates; intervals condition on fixed models and observed session composition.

A post-protocol temporal-role review found one44-second session preceding the original training. The original registered26-session result is preserved in [robustness.json](results/oos/robustness.json); current25-session chronological tables exclude it and disclose the diagnostic separately. [Transparent addendum](research/EXTERNAL_PROTOCOL_ADDENDUM.md). This does not affect the first next-day validation or change model/filter settings.

## 5. First External Validation

External interval: **2026-10-08 01:56:14.396905–02:39:50.017688 UTC**. All eligible times are evaluated; there is no external training split.

| Horizon | Labels / direction N | Original test OBI BA | External majority BA | External past-price BA | External OBI BA [60s95% CI] | Combined BA | OBI AUC |
|---|---|---:|---:|---:|---|---:|---:|
| 1s | 2,612 / 438 | 0.799 | 0.500 | 0.616 | 0.909 [0.879,0.938] | 0.909 | 0.961 |
| 5s | 2,604 / 1,192 | 0.728 | 0.500 | 0.565 | 0.800 [0.758,0.837] | 0.799 | 0.871 |
| 10s | 2,594 / 1,708 | 0.695 | 0.500 | 0.544 | 0.726 [0.680,0.767] | 0.726 | 0.798 |

At1s,2,174 of2,612 labels are unchanged (83.2%); the remaining438 have180 down/258 up. OBI Accuracy is0.904 and confusion matrix is`[[169,11],[31,227]]`. These are **438 conditional direction observations**, not90% correct on every second. Original test56 came from512 labels minus456 zeros; the external sample is larger partly because the entire43.6-minute session is scored rather than the original8.5-minute test window.

At1s the lowest/highest original-training OBI bins have mean returns−0.124/+0.180bps and unconditional up probabilities1.5%/32.4%. Bin means rise monotonically in this external session at all three horizons. The paired60s-block BA-gain CI versus the past-price rule is[0.259,0.330] at1s; this candidate supports the relationship under the stated block assumptions. It has44 one-minute blocks versus9 in the original test, **but still only one new date**.

[All models, matrices, rates, quantiles and block sensitivities](research/INDEPENDENT_VALIDATION.md).

![OBI bins and forward returns](results/oos/quantile_return.png)

![OBI bins and up probability](results/oos/quantile_probability.png)

## 6. Date and Session Robustness

Current tables are forward-only; the pre-training diagnostic and final reserved session are excluded. Daily intervals stratify blocks within observed session-date units and are not new-day generalization intervals.

| UTC date | Horizon | Direction N | Past-price BA | OBI BA [60s95% CI] | Combined BA |
|---|---|---:|---:|---|---:|
| 2026-10-07 | 1s | 8,684 | 0.638 | 0.887 [0.878,0.895] | 0.887 |
| 2026-10-07 | 5s | 22,648 | 0.566 | 0.757 [0.746,0.768] | 0.757 |
| 2026-10-07 | 10s | 30,377 | 0.543 | 0.695 [0.683,0.706] | 0.695 |
| 2026-10-08 | 1s | 3,724 | 0.628 | 0.888 [0.877,0.899] | 0.888 |
| 2026-10-08 | 5s | 9,521 | 0.565 | 0.771 [0.755,0.786] | 0.770 |
| 2026-10-08 | 10s | 12,665 | 0.545 | 0.705 [0.686,0.721] | 0.704 |

Pooled direction counts are12,408/32,169/43,042 at1/5/10s; pooled OBI BA is0.887/0.761/0.698. These counts are not independent information units. At each horizon17 of25 forward-only sessions have both directional classes, and OBI has a higher BA point estimate than the past-price rule in all17. Eight have undefined two-class BA and are retained in the report. Some scores use only a handful of moves; a score of1.0 is not a reliability claim. Session-level dispersion is wider than the date aggregates, and no independent sign test across sessions is claimed.

- Direction BA generally declines from1s to10s. Correlation and mean-return magnitudes need not decline monotonically.
- Combined features offer no repeatable material improvement.
- High trailing-past-volatility strata have weaker OBI point scores. This is descriptive, with changing class/session composition.
- The fixed original-training spread cutoff leaves the low-spread group extremely sparse; it cannot establish a spread-regime effect.
- Tight TTL1s, lag<=0.5s and every-other-second decisions leave similar scores in these observed cohorts, but change retention and do not identify causal latency effects.

[Every session, regime and sensitivity result](research/ROBUSTNESS.md) · [chronological JSON](results/oos/chronological_robustness.json) · [model CSV](results/oos/session_model_metrics.csv).

![Horizon and frozen-model performance](results/oos/horizon_performance.png)

![Every forward-only session](results/oos/session_performance.png)

## 7. Interpretation and Limitations

The original positive OBI relationship reproduced on the predesignated next-day session and appears in both observed-date aggregates. This supports an empirical relationship **within these admitted observations**. It does not validate broad performance across independent dates or market regimes. The two dates, persistent state, overlapping5/10s labels, clock-selected exclusions, small original training set and already-seen secondary analyses limit inference. Pointwise block intervals are not multiple-testing-adjusted and omit training/between-day uncertainty.

No executable profit is established. Mid is not a tradable price; spread, fees, latency, adverse selection, queue position, cancellation/fill probabilities and own-order impact matter. This project did not measure realized slippage, market impact or queue/fill outcomes, and has no execution simulator. Preserve the final reserved session and obtain several truly new dates before redesigning models or making generalization claims.

## 8. Reproduction

Python3.11+; no original-project imports or original virtual environment required. `requirements-audit.txt` records the independently verified Python3.11 environment. Original direct-version records in `requirements-reproduction.txt` require Python>=3.12. Raw data are required for full replay and are not bundled.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q

# ROOT is the existing raw Hyperliquid bbo/BTC folder (contains date/hour subfolders).
python research/oos.py inventory --bbo-root /path/to/bbo/BTC
# Saved frozen_models.json is supplied. Evaluation does not fit models:
python research/oos.py first --bbo-root /path/to/bbo/BTC
python research/oos.py robustness --bbo-root /path/to/bbo/BTC
python research/chronological_robustness.py --bbo-root /path/to/bbo/BTC
python research/report_oos.py
```

The inventory reconstructs the ignored input manifest and must match registered fingerprints. Evaluation checks model/protocol/source hashes and source files before/after reading. It refuses a changed evaluation code/model bundle; do not silently alter the protocol to rerun after seeing scores. `freeze` is the original-training-only recreation stage used before outcomes, and asserts equality to an existing saved bundle rather than overwriting it. Exact bundle-regeneration metadata is environment-specific; ordinary replay uses the saved coefficients. The chronology correction is separately hashed and transparent. Reserve handling remains fixed on replay.

Original pilot replay remains available through `research/run.py --bbo-dir ... --recorder-dir ... --output-dir ...`; the original timing/sample audit is `research/audit.py`. Historical outputs are preserved. [Verification](research/VERIFICATION.md) records tests, source/input fingerprints and repeatability checks.

## 9. Portfolio and Provenance

[English title, stack, two resume bullets, findings, limitations and interview decisions](research/PORTFOLIO_SUMMARY.md) · [reuse provenance](PROVENANCE.md) · [original asset audit](research/ASSET_AUDIT.md).

All source data are read-only; no collector, dashboard, orders, commit or push is part of this study. AI assistance covered implementation, analysis and documentation; the included checks establish explicit contracts, not exchange authenticity or trading profitability.
