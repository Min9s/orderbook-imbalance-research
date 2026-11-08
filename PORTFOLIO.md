# Portfolio summary

**One-sentence introduction**

A reproducible BTC market-microstructure study that separates order-book imbalance's conditional predictive information from all-time decision coverage and executable trading profitability.

**Resume bullets**

- Audited 682,024 observed BTC BBO updates and implemented receive-time features, purged chronological evaluation and frozen-model external validation, documenting degradation in a 77,143-update final temporal holdout.
- Distinguished conditional direction scores from all-observation information using paired time-block uncertainty, zero-return coverage and predeclared spread/deferred-markout diagnostics, without claiming realized execution profitability.

**30-second explanation**

I studied whether best-level order-book imbalance predicts BTC mid-price changes over one to ten seconds. I reused observed BBO data, froze simple logistic models before external evaluation, and checked timing leakage and dependent-label uncertainty. Final conditional Balanced Accuracy fell to 0.764, 0.625 and 0.577. Including unchanged prices and deferring the markout changed the interpretation further. The contribution is a transparent, reproducible test of predictive information and its execution limits, not a profitable trading system.

**Three technical choices**

1. Receive-time as-of features and exact clock-time labels with stale-quote checks and strict purging.
2. Simple frozen Logistic models with training-only preprocessing, explicit temporal roles and an irrevocably consumed Holdout.
3. Paired session-date clock blocks and separate conditional/all-time estimands, with executable-price assumptions kept out of performance claims.

**Three limitations**

1. Only two UTC dates; the final interval is later on an already observed date, so block intervals do not establish independent-day generalization.
2. Conditional scores exclude future zero returns; all-time coverage, class frequency and clock-based censoring change the inference.
3. BBO does not establish fills, queue position, slippage, market impact, paid fees or net profitability; exact historical replay requires unbundled private inputs.

**Repository:** https://github.com/Min9s/orderbook-imbalance-research

[Detailed hypotheses and five interview questions](research/final_v1/PORTFOLIO.md) · [Research report](research/final_v1/REPORT.md)
