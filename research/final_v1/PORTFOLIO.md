# Portfolio and interview summary — final-v1

**Project title:** Order Book Imbalance and Short-Horizon Price Predictability in BTC Markets

**Stack:** Python3.11, NumPy, PyArrow/Parquet, scikit-learn Logistic Regression/StandardScaler, Matplotlib, pytest; immutable JSON models/protocols, SHA-256 input/source checks, paired session-date time-block bootstrap.

## Resume bullets

- Audited 682,024 observed BTC BBO updates and built a reproducible L1 microstructure study with receive-time feature availability, purged temporal splits, frozen-model external validation, and an explicitly consumed 77,143-update final holdout.
- Distinguished conditional price-direction prediction from all-observation information and decision coverage, reporting material final-period performance degradation rather than tuning models after test disclosure.
- Analyzed training-only imbalance-bin forecasts against quoted spreads and a predeclared deferred-markout sensitivity, documenting why BBO predictability does not establish fills, market impact, or executable net profitability.

## Verified research outcomes and hypotheses

The primary hypothesis concerned direction conditional on a nonzero future return; the final1s OBI BA was0.764 with60s pointwise block CI[0.746,0.781], above fixed baselines but below0.909 in the earlier external session.
The exploratory hypothesis concerned unconditional information: extreme OBI bins showed different mean returns and up/down probabilities with zeros retained, but10s middle-bin means were not universally monotone and the binary score did not model move occurrence.
The execution analysis found a gap between training-bin forecast magnitudes, current quoted gaps and deferred markouts; these were descriptive comparisons, not fill simulations or PnL.

## Limitations

Onlytwo UTC dates are archived; the final interval is on an already observed date, so neither session counts nor narrow within-session intervals establish independent-day generalization.
Conditional-on-move classification, changing flat-price rates, overlapping labels, persistent state, clock-based censoring and a small original training set constrain inference and calibration.
Raw redistribution permission, certified UTC/network latency, actual paid fees, queue position, slippage, fill probability and own-order impact were not established; the consumed Holdout cannot be reused as unseen validation.

## Five Quant Research interview questions

1. Why can `P(up | move, X)` be high while all-time decision accuracy or usefulness is limited, and how do you distinguish outcome coverage from ex-ante participation coverage?
2. How do receive-time as-of selection, valid-path labels, session boundaries and strict purging prevent future information from entering a feature or crossing evaluation splits?
3. Why do overlapping returns and persistent OBI require block-based uncertainty, and why do120 clock blocks not replace independent trading dates?
4. Why is Microprice offset algebraically related to OBI and Spread, and what does final-period deterioration say about feature information, target frequency and magnitude calibration?
5. What assumptions separate a signed mid-price markout or forecast-versus-gap comparison from a tradable return, and what extra order/queue/fill data would be needed to test execution feasibility?
