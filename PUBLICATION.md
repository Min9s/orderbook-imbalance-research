# Publication scope and verification

This repository publishes **research code, technical documentation and aggregate evidence**.
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

The dated original release checks are recorded in
[PUBLICATION_VERIFICATION.md](PUBLICATION_VERIFICATION.md). Current checks run in
[public verification CI](https://github.com/Min9s/orderbook-imbalance-research/actions/workflows/public-verification.yml).

## Publication manifests and historical records

Two manifests serve different purposes:

- [PUBLICATION_FILES.json](PUBLICATION_FILES.json) is the original, unchanged
  107-entry `publication-v1` snapshot. Its paths refer to commit
  [`587eb6c69b422a347612aaf83bb00c155f21a030`](https://github.com/Min9s/orderbook-imbalance-research/tree/587eb6c69b422a347612aaf83bb00c155f21a030),
  including files intentionally removed from the current presentation.
- [PUBLICATION_CURRENT.json](PUBLICATION_CURRENT.json) inventories the current
  public package. It excludes itself to avoid a circular hash and identifies the
  original snapshot separately. It does not replace any experimental fingerprint.

Run `python examples/verify_publication.py` from the checkout. It checks current
file sizes, SHA-256 hashes and exact nonignored Git working-tree membership,
including pending additions and excluding pending deletions. It then checks the
original manifest's identity and all 107 historical entries against Git objects,
with exact snapshot membership. Missing history is an error, not a skipped check.
Ordinary clones include the history; for a shallow clone, first run
`git fetch --unshallow origin`. CI explicitly fetches full history.

The original manifest SHA-256 is
`baaac3e9be8a01f51325dc08004bee400d589e61cc1d453af2eaf7a91205697e`.
No archived file is resolved against the current tree or copied into a new
archive directory. For example, the pre-final README remains available
[verbatim in its historical snapshot](https://github.com/Min9s/orderbook-imbalance-research/blob/587eb6c69b422a347612aaf83bb00c155f21a030/research/final_v1/README_before_final.txt).
Resume drafts, interview notes and superseded presentation graphics remain in
that same Git snapshot. Git history has not been rewritten.

Historical reports retain their experimental stages: the pilot audit, first
external validation, chronological correction and final consumed holdout answer
different questions. Earlier references to a reserved holdout, earlier test counts
or no commit/push describe those dated stages. The
[final consumption record](results/final_v1/consumption.json) is authoritative;
it is unchanged. Frozen sources, protocols, model parameters and all 47 result
files retain their original bytes. Only current navigation and publication
verification are updated; the final report generator's footer follows that
navigation without changing calculations or figures.

The current manifest must be updated only after an explicit file review. Do not
populate it from arbitrary local directories, include ignored private inputs, or
rewrite historical hashes to make a changed experiment pass. These checks verify
byte integrity and package scope, not independent data authenticity or externally
timestamped preregistration.
