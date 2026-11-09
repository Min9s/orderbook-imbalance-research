# Current data-access status — final-v1

The original Hyperliquid BTC BBO archive remains read-only outside this project.
Its28 session IDs span only2026-10-07/08. All3173 files and their SHA-256 hashes
are part of the recorded inventory; final replay verifies the unchanged archive.
No original project code, virtual environment or hardcoded original absolute path
is required. Pass a relocated normalized BBO root with date/hour subfolders.

The original-source/API/rights inspection is documented in the
[historical data-access review](../DATA_ACCESS.md). No new raw-data redistribution
grant or exact public historical-download URL has been established. Raw BBO and
row-level derived predictions are not bundled or uploaded. A public clone can run
the [public test suite](../../tests/) and inspect aggregate/model/protocol evidence without raw inputs, but
full market replay needs the original archive. New public BBO observations would
reproduce the method, not the historical numerical results.

For a clone with the complete unchanged archive, reconstruct only the ignored
input manifest; this does not overwrite any numeric inventory or old result:

```bash
python research/final_v1/rebuild_manifest.py --bbo-root /path/to/bbo/BTC
python research/final_v1/run.py replay --bbo-root /path/to/bbo/BTC
python research/final_v1/run.py explore --bbo-root /path/to/bbo/BTC
python research/final_v1/report.py --bbo-root /path/to/bbo/BTC
```

The final77,143-row interval has now been consumed. Prior documents labeling it
reserved describe earlier versions, not current availability. The immutable
consumption ledger is in `results/final_v1/consumption.json`; replay never makes
it unused again. No raw data were newly collected. Additional genuinely new dates
are necessary before redesigning the model and claiming another independent test.

The experiment remains BBO research: no exchange account, API key, order submission,
queue observation, real fills, slippage/impact measurement or paid-fee evidence is
present. Source/exchange timestamps and local receive wall clocks do not certify
pure network delay or synchronized UTC. The observed-clock distribution and
assumed deferral are explicitly labeled separately from measured execution costs.

The public release additionally omits historical event-level prediction CSVs and
execution logs. Aggregate-only public tests do not reconstruct ranking AUC from
confusion matrices. Some historical pilot/audit commands need those private audit
files as well as raw data; final frozen-model replay needs the unchanged raw archive.
