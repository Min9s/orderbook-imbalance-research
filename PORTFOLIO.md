# Portfolio summary

## 현재 소개와 과거 기록 읽기

프로젝트의 한국어 개요·구조·실행 방법은 [README](README.md), 최종 실험의 해석은
[한국어 요약](research/final_v1/SUMMARY_KO.md)과 [최종 보고서](research/final_v1/REPORT.md)를 기준으로 읽으세요.
아래 영문 소개와 [최종 면접 질문](research/final_v1/PORTFOLIO.md)은 같은 최종 평가 범위를 설명합니다.
[초기 소개](research/PORTFOLIO_SUMMARY.md), [초기 이력서 문장](research/RESUME_BULLETS.md),
[평가 전 README](research/final_v1/README_before_final.txt)는 과거 시점의 기록입니다.
과거의 reserved holdout 표기는 현재 미사용 검증 데이터가 남아 있다는 뜻이 아닙니다.
기록과 검증 근거를 보존하기 위해 파일을 삭제하거나 이동하지 않았습니다.

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
