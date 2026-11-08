# Data access and collection plan

## What is available now

The input is an owner's local Hyperliquid BTC perpetual BBO archive, not a third-party public historical download. It contains 682,024 rows across 28 session IDs in 3,173 Parquet files on 2026-10-07/08. This count is an inventory, not a declaration that every row is research-eligible. Some later sessions have negative exchange-to-receipt differences or large delays. The 42-minute pilot uses only 15,295 rows of one session; the rest of that same session is useful additional development data, not an independent session.

`results/audit/session_inventory.json` reproduces session counts, time ranges and lag extrema without computing returns or selecting by model performance. It can be regenerated with `research/audit.py --inventory-root /path/to/BTC`.

For a prospective holdout, the fixed quality-only rule chooses the earliest session starting on the next UTC day with at least 30 minutes duration:

- Session `95a74716c1c140eb8e896cb11f924151`.
- 2026-10-08 01:56:14.396905–02:39:50.017688 UTC, 16,945 BBO events, 43.6 minutes.
- 2,614 valid of 2,616 1-second grid states, 4 receipt gaps >2 seconds, no invalid quote/clock/sequence/payload observations in the inspected rows.
- Existing recorder log: `Liquidation_gravity/data/interim/market_recorder/eea0f5caeba34035aa50598280ceb837/events.jsonl`, connection at 01:56:14.219604 UTC. A subsequent disconnection is logged at 02:44:31 UTC, after the observed BBO series ends. The unobserved tail must not be invented or labeled.
- **No returns, model scores, or tuning on this candidate were performed during this audit.** It is temporally disjoint and a different session/day, but statistical independence and loss-free coverage are not established. It is suitable for a next frozen-model validation attempt, not proof that validation already succeeded.

The initial pilot session continues until 07:44 UTC with 55,310 total rows. Several later same-day sessions span approximately three hours. Those can support stability checks under frozen rules, subject to their own clock/gap audits. Repeating random splits of the pilot is not a substitute.

## Source and rights review — 2026-11-08

Official [WebSocket subscriptions](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions) describe `bbo`, its coin/time/bid-ask structure and updates when BBO changes on a block. A quiet interval is therefore not by itself proof of packet loss. [Rate limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits) document public API connection/subscription limits. These are access documentation, not a historical-data redistribution grant.

The official [Interface Terms of Use](https://app.hyperliquid.xyz/terms), displayed update June 15, 2026, were inspected from the site's own JavaScript because the HTML page is client-rendered. The asset was `https://app.hyperliquid.xyz/assets/TermsOfUse-BNJf3aEI.js`, 42,673 bytes, SHA-256 `8c766aa36c5265548dd63d9f147a007be452a033724c4cf13c68525960728abe`. The text addresses interface access, automation abuse and information accuracy. No explicit public redistribution grant for this historical BBO archive was found in that inspected text. This does not establish either that redistribution is prohibited or that it is permitted, nor does an interface agreement alone determine every API-data right. The record is a limited source inspection, not legal clearance.

Consequently no raw data is added to the public project. There is **no verified freely redistributable download URL for the exact pilot inputs**. A public clone can run numeric/leakage tests and verify stored test metrics, but cannot regenerate this market experiment without the inputs. Publish raw files only after permission or an applicable license is established. Numerical summaries/figures are already present; their publication does not establish rights to distribute the underlying archive.

## Smallest public acquisition route

The public endpoint `wss://api.hyperliquid.xyz/ws` accepts the subscription:

```json
{"method":"subscribe","subscription":{"type":"bbo","coin":"BTC"}}
```

A new capture reproduces the method, **not the original historical prices**. This audit did not start a collector. No new collector implementation is needed. Existing `api/hyperliquid.py:subscriptions` and `collectors/market.py:MarketRecorder` already support a single-asset/single-channel bounded run. `scripts/collect_market.py` accepts `--assets BTC --channels bbo --duration-seconds ... --raw-root ... --status-root ...` and checks its existing `live_enabled` configuration. Preserve that check; use a separately reviewed enabled configuration and separate output directories when a future collection is authorized. Existing files/configurations need not be modified.

For example, after the owner's existing collection configuration is reviewed:

```bash
# Future collection example only; NOT executed during the audit.
python scripts/collect_market.py --config /path/to/reviewed-collection.yaml \
  --assets BTC --channels bbo --duration-seconds 7200 \
  --raw-root /path/to/new-capture/raw --status-root /path/to/new-capture/status
```

This command belongs to the original collector project/environment; running the independent analysis project does not require importing or installing that collector.

## Recommended additional observations

First evaluate the already available next-day candidate with the original pilot-trained models and fixed preprocessing/thresholds; do not refit on the candidate and call it a holdout. Freeze a primary metric/horizon in advance (e.g. the existing 1-second OBI direction metric), retain all horizons as secondary, and report zero-return coverage and class counts on every session.

A practical initial target is **5–10 distinct UTC dates, at least 1–2 contiguous hours per date**, preferably across different times of day and both calm and volatile conditions. This is a planning recommendation, not a power guarantee. The pilot's approximately 8.5-minute test region supplies only 9 one-minute blocks. Two hours would give 120 such blocks for a frozen-model external test, although adjacent blocks may remain dependent; per-day/session replication is more valuable than counting more ticks in one market episode. At the pilot's test directional rate (56/512), two hours might contain roughly 790 nonzero 1-second labels, but this extrapolation is uncertain and should not determine stopping after seeing significance.

For a rough design illustration only, 30 independent paired blocks with standard deviation 0.2 in block-level accuracy gain would give a mean-gain standard error near `0.2/sqrt(30) = 0.037` (normal 95% half-width about 0.072). The true variance, intraday dependence, unequal event counts and target effect are unknown; obtain these from additional predesignated sessions rather than infer adequate power from 15,295 ticks. A precise power calculation cannot be justified by this pilot alone.

Before capture, fix duration/session rules without looking at returns. Preserve:

- exchange `time` in original milliseconds and local receive wall-clock ns;
- local monotonic receive clock and clock-step diagnostics if the existing capture path supports them; do not fabricate these for historical records;
- full raw WebSocket payload/channel, coin, bid/ask px/sz/order counts, source endpoint and event hash;
- session/run IDs, subscription requests/acknowledgements, heartbeat/disconnection/reconnection and storage diagnostics;
- unaltered original units/precision, receipt order, schema version and file hashes;
- host clock synchronization/jump records. Subsecond labels are sensitive to a 261ms median observed exchange–receive difference; without trusted clock alignment that difference is not a pure network-latency measurement.

Do not merge reconnects into one uninterrupted path, relax age checks to gain sample size, or replace BBO quantities with volume/liquidation values.

## External-v1 update (after the quality-only audit)

The formerly quality-only next-day candidate has now been evaluated with frozen
original-training models; results are in INDEPENDENT_VALIDATION.md. The earlier
quality-only statements describe that prior stage, not the current data status.
The full archive inventory confirms **2 distinct UTC receive dates,28 sessions,
682,024 rows and3,173 files**. One session crosses midnight, so daily session
appearances total29. All raw numeric quotes are complete, but67,059 negative
exchange→receive differences and6,036 differences>2s make unqualified pooling
inappropriate. Full per-session timing/admission checks: EXTERNAL_INVENTORY.md.

The entire55,310-row original session is excluded from external aggregates.
The latest77,143-row session `df37f36553464010ae9c34cd83d0eeac` remains reserved:
its source/quality was inspected but no forward-return labels or model scores
were computed. Its interval is2026-10-08 15:15:56.594595–17:15:56.455088 UTC.
A325-row pre-training session is retained only as a retrospective diagnostic;
the original broader registered aggregate and the transparent temporal-role
correction both remain available. The25 forward-only sessions contain549,246 raw
BBO and66,679 valid1-second feature states, with only one genuinely new date
relative to the original study.

No new collector was implemented or launched. Raw inputs remain outside this
repository; local event-level external predictions are in ignored `data/`.
Rights review conclusions have not changed: no raw-data upload or public exact
historical download is asserted. The frozen evaluation uses independently
installable analysis code, not the collector environment. A future redesign
must treat the now-evaluated sessions as seen and retain the reserved final;
additional distinct dates remain necessary even if within-date block CIs narrow.

The reserved final interval is on the already observed Oct8 calendar date. It is
an unused temporal segment, not a third independent date; several genuinely new
dates are still required for broader generalization.
