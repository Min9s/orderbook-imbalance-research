# Publication scope and verification

This repository is a public **code, documentation and aggregate-evidence portfolio**.
It does not redistribute the underlying market archive.

## Included

- Locally authored analysis/tests and the owner's small reused quote-feature function.
- Frozen coefficients, preprocessing/protocol records and dataset fingerprints.
- Aggregate performance, class counts, session/date summaries and research figures.

## Excluded

- Raw BBO files, normalized event-level data and all event-level prediction CSVs.
- Input manifests, private derived Parquet caches, API credentials and secret files.
- Virtual environments, Python/test caches, packaging metadata and execution logs.
- Machine-specific absolute paths; nonnumeric machine metadata was redacted in this public copy.

Original research files remain in a separate local archive. Protected evaluation
sources, frozen models, Primary Holdout JSON, protocol and consumption hashes are
unchanged. Historical byte-replay statements concern the recorded experiments;
they do not assert that redacted machine metadata is byte-identical to the local
archive. No model, threshold, target or statistical result was changed for release.

## Data rights and source status

The maintainer authorized public publication of their personal research code and
documentation. The prior source-provenance record states ownership/authority over
the original personal implementation. No open-source license has been assigned;
public availability is not an MIT-style license grant.

The official [Hyperliquid API documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions)
documents BBO access. The [Interface Terms](https://app.hyperliquid.xyz/terms) were
rechecked on 2026-11-08 through the site's own rendered-content asset (SHA-256
`8c766aa36c5265548dd63d9f147a007be452a033724c4cf13c68525960728abe`). No raw-archive
redistribution grant was established. This is a bounded source inspection, not
legal clearance or a license for the omitted archive. Only non-event-level
research outputs accompany the code; no source-data license is asserted.

## Public verification versus private empirical replay

`python examples/verify_public_results.py` uses only the standard library and
published aggregate evidence. Tests validate calculations with invented quotes,
published confusion matrices, protocol/source hashes and temporal-role invariants.
Neither operation recreates the market experiment, ranking AUC or source clocks
from raw observations. The optional private prediction audit runs only when its
unpublished row files are present; it is not needed by the public suite.

Full empirical replay requires the complete unchanged private archive. It is
hash-checked against the recorded fingerprint. The final Holdout is consumed;
replay is repeatability verification, never a new independent evaluation.

Fresh-environment commands and final release checks are recorded in
[PUBLICATION_VERIFICATION.md](PUBLICATION_VERIFICATION.md). The public tree is
checked against an explicit file manifest before committing and pushing.
