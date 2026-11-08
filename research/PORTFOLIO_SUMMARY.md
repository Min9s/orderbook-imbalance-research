# Portfolio summary

**English title:** Order Book Imbalance and Short-Horizon Mid-Price Prediction

**Stack:** Python3.11, NumPy, PyArrow/Parquet, scikit-learn Logistic Regression and StandardScaler, Matplotlib, pytest; JSON model/protocol fingerprints and paired clock-block bootstrap.

## Resume bullets

- Audited 682,024 observed Hyperliquid BTC BBO updates and built a reproducible L1 imbalance study, separating 25 forward-only evaluation sessions from original research, a retrospective diagnostic, and an unused final holdout.
- Recreated and froze training-only logistic models for 1–10 second mid-price direction, validating on a 16,945-quote next-day session and reporting paired time-block uncertainty, zero-return conditioning, and one-new-day generalization limits.

## Key findings — three sentences

The original positive OBI relationship reproduced on a predesignated next-day session, where the frozen model achieved conditional directional Balanced Accuracy of0.909/0.800/0.726 at1/5/10seconds.
Chronological date aggregates also showed positive monotone OBI-bin return relationships, while direction performance weakened at longer horizons and the combined-feature model showed no material consistent benefit.
Clock-quality exclusions, explicit temporal roles, fixed-model replay and transparent block sensitivity make the results reviewable without converting conditional prediction into a trading-profit claim.

## Limitations — three sentences

The archive contains onlytwo UTC dates and one new validation date, so neither28 session IDs nor narrow within-session block intervals establish broad market-regime generalization.
Direction scores exclude zero future returns, label windows overlap, absolute clock alignment is uncertified, and secondary regime analyses remain descriptive.
Queue position, realized fills, slippage and market impact were not measured, while exact historical replay requires non-bundled raw inputs whose redistribution rights were not established.

## Five interview decisions

1. **Availability and clocks:** explain receive-time as-of versus exchange-time order, why261ms observed clock difference is not certified latency, and how stale/invalid observations block labels without interpolation.
2. **Feature scope and reuse:** explain L1 OBI versus trade/liquidation imbalance, the reused LG function, and why microprice offset is the OBI×spread interaction rather than independent information.
3. **Frozen estimation:** explain original chronological splitting/purging, training-only scaler and quantile cutoffs, deterministic model recreation, probability verification, and no external fit or threshold tuning.
4. **Target population:** explain why56 original test moves became438 in a full external session, and why nonzero-future-return conditioning does not give a deployable unconditional accuracy.
5. **Independent evidence and honest correction:** distinguish sessions from dates, conditional time-block uncertainty from new-day uncertainty, the disclosed removal of a pre-training session from chronological aggregates, and preserving a genuinely unused final evaluation session.
