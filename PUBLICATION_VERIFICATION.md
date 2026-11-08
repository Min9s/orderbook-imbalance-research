# Publication verification — 2026-11-08

## Fresh standalone environment

A new Python 3.11 virtual environment was created for the clean public checkout.
`pip install -e '.[dev]'` completed with dependencies resolved independently.
The imported `obi_research` package was confirmed to come from that checkout,
not Liquidation Gravity, the OMS project or the original research environment.
Exact installed versions are in [publication_environment.json](results/publication_environment.json).

- Complete public suite: **33 passed**, no skipped tests.
- `python examples/verify_public_results.py`: passed; standard-library aggregate,
  model/source/consumption and recorded archive-fingerprint consistency checks.
- The same example also passed with a base Python interpreter outside the venv.
- `pip check`: **No broken requirements found**.
- In the fresh environment, a separate local-only audit recomputed Accuracy,
  Balanced Accuracy, ROC-AUC and matrices for **12 final model/horizon results**
  from private cached prediction rows; all matched exactly. Those rows are not
  part of the public tests or repository. No model was fitted or retuned.

## Scope and source checks

Public candidates were scanned for private absolute paths, credential/key patterns,
raw/event-level files, execution logs and oversized files. No matching private
paths, secret candidates or forbidden market files remained. Models, numeric
Primary/exploratory JSON, protocol/consumption records and protected source hashes
were compared with the separate local archive and remain unchanged.

Only documentation, the public aggregate-test branch, a standard-library example
and machine-path redactions changed for publication. The optional private-row
verification remains available locally; public consistency checks do not recreate
ranking AUC or raw-clock quality. All Markdown links and four README figures were
checked. Historical local evidence is preserved separately; no original LG or OMS
source was modified.

The final interval remains consumed; the two-date and conditional-target limits
are retained. Deferred markouts and quoted-gap comparisons are not measured
execution latency, fills, fees, slippage, impact, or PnL. Data access/rights
boundaries are explicit in [PUBLICATION.md](PUBLICATION.md).

## Commit and remote verification

The release file list is explicitly reviewed before staging. The repository is
created independently, with public code/docs/aggregate evidence only. Remote main
and README are checked after push. Release verification establishes the recorded
code/data-boundary and repeatability checks, not legal clearance for omitted raw
data, statistical market-wide generalization, or trading profitability.
