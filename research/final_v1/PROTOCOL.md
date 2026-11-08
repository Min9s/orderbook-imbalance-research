# Final-v1 protocol — before final Holdout disclosure

This local record separates the unchanged conditional-direction Primary A from newly defined exploratory B. It is not an externally timestamped registration. The saved prior final session has not yet been scored when this protocol is written.

## Fixed Primary A

A asks whether direction is predictable **conditional on a future nonzero return**. Use the saved original-training coefficient/scaler bundle, same feature definitions, same1s grid, same1/5/10s horizons, same strict quote/path rules, threshold0.5 and existing baselines. The primary endpoint is1s OBI Balanced Accuracy with paired gain versus original-training majority; other horizons/metrics are secondary. No fitting or model selection is allowed on Holdout.30/60/120s blocks and half-block shifts are disclosed;60s is the main pointwise interval.

## Exploratory B, fixed before disclosure

B asks about information at **all admissible decision times**, including unchanged outcomes. The frozen Logistic score is P(up | move, features), not P(up | features), and is not a magnitude forecast.

- Keep all zero returns in unconditional return means and up/down/flat proportions. Direction-only results remain A and cannot be compared numerically with three-action agreement as if denominators were identical.
- Report feature availability = valid grid/all grid, label availability = valid labels/possible in-session grid pairs, and nonzero outcome fraction. The nonzero fraction is a retrospective outcome coverage, not an ex-ante trigger.
- Report decision activity both on all valid feature states and on valid labeled states. A fixed confidence policy acts up if p>0.6, down if p<0.4, and otherwise abstains. It is not tuned. Forced direction at p>=0.5 and a constant all-time training-majority class are comparators.
- Code actions as−1/0/+1 solely for descriptive three-action accuracy, fixed3-class macro recall and matrices. Abstention is not a trained probability of a flat price or an economic utility. Report all-time up-versus-not-up rank AUC as discrimination only, not probability calibration.
- For forecast magnitude, use original-training all-label mean forward returns in the original5 OBI bins. This new exploratory lookup is separate from the unchanged Logistic. No external return enters those means or cutoffs.
- Compare forecast absolute bps and realized signed mid changes with current full quoted spread_bps. A full instantaneous gap is a rough symmetric round-trip crossing-cost proxy, not a measured future fill cost. Extra0/1/5bps costs are assumed round-trip scenarios, not actual exchange fees. No PnL/backtest is reported.
- Conservative sensitivity retains the original feature at t but measures log(M(t+1+h)/M(t+1)). Require the entire t..t+1+h path valid, both benchmark quotes' receive/exchange times strictly after t, and no session/date crossing. This assumes a1s deferral, not measured order-entry latency; future benchmark prices are outcomes only.
- Use original-training lag/relative-spread/past-volatility medians; also original-training absolute-spread median. Preserve sparse/unknown strata. All-time moments use session-date-stratified60s block intervals, not day bootstrap.
- Report25 previously seen chronological sessions separately from the consumed final session. Also report a predeclared sensitivity retaining only previously seen sessions with>=100 nonzero1s labels; do not choose whichever result looks best.

## What remains comparable

Primary A uses exactly the old estimator/target/metrics and can be compared with prior conditional test/OOS results, with differing periods and cohort sizes disclosed. Quantile mean returns and up probabilities already included zeros and remain definitionally comparable. B's three-action agreement, confidence-policy coverage, training-bin magnitude lookup, spread comparisons and deferred markouts are new exploratory estimands; they do not replace Primary A or represent a model improvement.

## Holdout and fingerprints

Holdout:77,143 BBO,2026-10-08 15:15:56.594595–17:15:56.455088 UTC, session `df37f36553464010ae9c34cd83d0eeac`. This is a new temporal segment of an already seen calendar date, not a third independent day. Prior quality inspection recorded7,200 grid states/7,041 valid states; no return or prediction score was inspected.

Model SHA-256: `a113817a95b9eee78df3f9a864b15e02217e2d2d4460fe0ecc7334087d5bdb20`. Registration time: `2026-11-08T07:38:22.073018+00:00`. Source hash and training-only magnitude mappings are in [protocol.json](../../results/final_v1/protocol.json).

Consumption is written before first labeling. A completed score is immutable and permanently seen. Explicit replay verifies the same fixed calculation and cannot turn this interval back into unused evaluation data. Old result files remain unchanged.
