# Frozen external-validation protocol — obi-external-v1

This local protocol was written before inspecting any new external-session predictions in this phase. It is not an independently timestamped registry. The candidate was previously quality-only. No external fitting/tuning is permitted.

JSON protocol SHA-256: `87d4f6eef8e458081363cf3f78bde430439b947e01ff64898b47410037c4e6e3`.
Frozen model SHA-256: `a113817a95b9eee78df3f9a864b15e02217e2d2d4460fe0ecc7334087d5bdb20`.

## Fixed conditions

- **created_utc**: 2026-11-08T04:30:26.106159+00:00
- **primary**: First external session, 1s OBI balanced accuracy and paired BA gain over training-majority baseline
- **secondary**: 5s/10s, combined logistic, price-change baseline, quantile means and up probability; all disclosed
- **data_units**: Receipt UTC day within session. Never join session paths. Drop labels crossing UTC date boundaries.
- **exclude**: Entire pilot session excluded from external robustness; latest session reserved; all other sessions reported including empty/one-class results
- **zero_returns**: Kept in statistical quantiles and class coverage; excluded from direction-model fit and scoring
- **timing**: 1s receipt-clock as-of; max receipt age2s, exchange-to-receipt lag[0,2]s; valid entire label path
- **fit**: No new fit/preprocessing/threshold selection on external data; fitted parameter JSON only
- **baselines**: Frozen original-training up prior; sign of previous1s return, zero/missing -> that prior
- **uncertainty**: 1000 paired nonoverlapping clock-block bootstrap replicates at30/60/120s, origin0 and half-block shift; stratify by session-date, retain empty time blocks; no date bootstrap
- **regimes**: Causal trailing60s RMS past1s return (60 valid increments); spread/lag/vol low-high cutoffs from original training only; no parameter fitting on new sessions
- **sensitivity**: Fixed additional diagnostics only: receipt TTL1s, exchange lag<=0.5s, decision every2s with exact1/5/10s endpoints. Primary remains unchanged.
- **interpretation**: Only2 archived UTC dates and one new date; no independent28-day claim. Block intervals are exploratory conditional-on-model/session-composition; no multiple-testing correction or profitability claim.

## Original model recreation

Only the initial session's original 60% training interval, strict purge and nonzero-return rows reach LogisticRegression.fit. Training counts: 101/391/641 at1/5/10s. Both models reproduce the original test probabilities within1e-12 and all reported test metrics exactly before any new-session evaluation. No new-data scaler, quantile edges or parameter estimation occurs. C=1, lbfgs, max_iter=2000, threshold0.5; original constructor random_state=None (deterministic lbfgs), NumPy seed20261108 recorded. JSON stores feature order, scaler mean/scale, coefficients/intercept/classes and model/data/code fingerprints. Quantile cutoffs are original training-feature quintiles, including zero-forward-return observations as in the original pilot.

Features are mid=(bid+ask)/2, spread=ask−bid, relative spread=spread/mid, OBI=(qb−qa)/(qb+qa), microprice=(ask×qb+bid×qa)/(qb+qa). Predictors are OBI, or OBI+spread_bps+microprice_offset_bps. Microprice offset equals OBI×spread_bps/2. Features use last received<=t; future log returns use last received<=t+h. Both quantities must be positive, bid<=ask, finite, no invalid intermediate grid state. Both original numeric formulas and validated receipt-as-of rules remain unchanged.

## Split roles and reporting

- Original session e29a1088ea904b0f83335013adb7c384: training/validation/test and its entire later continuation are excluded from external robustness. This is stricter than excluding the first42 minutes only.
- First external 95a74716c1c140eb8e896cb11f924151: all eligible1-second decision times in the session, no retraining or internal split. One new date, not a new set of trading days.
- Reserved final df37f36553464010ae9c34cd83d0eeac: latest remaining session by receipt end time, chosen before scores. Only metadata/quality was inspected; do not compute returns or scores for it in this phase.
- Every other session is reported, including short/zero-directional/one-class sessions. None is selected based on performance. Sessions and UTC dates are never joined into a continuous path. Raw inputs remain external/read-only.
- Point metrics: Accuracy, Balanced Accuracy, ROC-AUC when two classes exist, confusion matrix with rows=true down/up and columns=predicted down/up. Empty directional cohorts yield null metrics; one-class BA/AUC are null. Report total up/down/unchanged before zero exclusion.
- Uncertainty: paired session-date-stratified clock blocks, not individual label resampling. No between-day CI is claimed from only2 dates. Primary intervals use60s;30/120s and half-block offsets are disclosed together. AUC is reported as a point statistic; confidence intervals cover Accuracy/BA and paired gains, correlation and quantile means/probabilities.
- Regime and stricter-filter diagnostics are secondary descriptive checks. No high-performing variant replaces the primary evaluation. Existing filters are never loosened. Any later redesign must treat these sessions as seen and keep the reserved final untouched.

## Later temporal-role addendum

After the registered robustness evaluation, one pre-training44-second session
was reclassified as retrospective rather than out-of-time. The immutable JSON
protocol and original aggregate remain unchanged. The corrected chronological
aggregate and exact reason are disclosed in
[EXTERNAL_PROTOCOL_ADDENDUM.md](EXTERNAL_PROTOCOL_ADDENDUM.md); this is not presented
as a pre-outcome exclusion. Frozen parameters and the first next-day evaluation
are unaffected, and no model/filter/threshold was retuned.
