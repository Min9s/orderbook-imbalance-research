# Provenance

`src/obi_research/legacy_book.py` is an unchanged extraction of the owner's
`Liquidation_gravity/src/liquidation_microstructure/microstructure/orderbook.py`.
It supplies `book_features` (OBI, spread_bps, log_depth). SHA-256: `a4276d7b9ba4a774b8b73a1211fd9046791346875d2c43ba253c442c042dfb3e`.
The new wrapper rejects zero on either side; the legacy helper permits zero on
one side. It adds midpoint, spread, relative spread and microprice.

Receipt-as-of selection and frozen file hash conventions were informed by LG
`research/inputs.py`; purging and fixed-time block bootstrap were informed by
`models/evaluation.py`. These small BBO-specific implementations were newly
written, not copied wholesale. The Toolkit's numeric and as-of contracts were
consulted; its collectors/OMS/synthetic venues were not imported or extracted.
No liquidation signal, wallet identifiers or synthetic market result is used.
The original repositories remain unchanged and are not runtime dependencies.

Original local BBO inputs remain outside this folder. Runtime input manifests
are local and ignored; summary.json includes an aggregate inventory fingerprint
and code/design hashes. The collector mainnet status/session logs support local
observed-data provenance but do not independently certify exchange authenticity,
UTC accuracy or complete event coverage. See research/ASSET_AUDIT.md.

Standard formulas are not claimed as original inventions. AI assistance covered
asset inspection, implementation, tests, analysis and documentation. The tests
check stated contracts; they do not establish real-world execution performance.
No license was inferred from source availability or API accessibility, and no
new license or raw-data redistribution grant is asserted.

## Follow-up audit

The original pilot artifacts and core source were preserved. `research/run.py`
now accepts portable BBO/evidence/output paths; original summary code hashes refer
to the earlier CLI version. `research/audit.py` refits the same frozen settings
and asserts equality to saved test probabilities and metrics, adds a requested
past-price-change baseline, and records sample/timing/block diagnostics. It does
not tune original models. `results/audit/` contains the separate evidence.
A fresh Python3.11 installation replayed copied inputs from another directory
without original-project imports. Documentation now distinguishes the original
Python3.13 direct-version record from the independently resolved audit environment.
No original collector source or virtual environment is needed to run the analysis.

## External-v1 evidence

The same unchanged LG feature function and original-training models are used for
external-v1. `results/oos/frozen_models.json` stores scaler/coefficient arrays,
training-data fingerprints and source hashes; `protocol.json` was locally recorded
before first-external scores. Neither original project is imported or modified.
Only JSON/CSV summaries, model parameters, protocol records and figures are public;
raw input manifests and local per-observation predictions are ignored by Git.

`research/oos.py` is a research runner, not a collector or general trading framework.
Its evaluation stages never fit an estimator. Session/date clocks, label boundaries,
stratified time-block uncertainty and original-model verification are explicit.
The source guard remains fixed after scores. The later pre-training-session role
correction is separately recorded in EXTERNAL_PROTOCOL_ADDENDUM.md and a separate
hashed script; it does not replace the original aggregate or retune any model.
At the external-v1 stage the latest session was reserved. Final-v1 subsequently
consumed that interval; the consumption ledger is authoritative. Only two observed
UTC dates remain, so all performance claims retain their limited empirical scope.

## Public portfolio boundary

The user explicitly authorized public publication of their research code and
documentation. The prior owner statement recorded in the original Toolkit
provenance identifies the source/current work as personal work with authority
to publish. No open-source license is inferred or newly assigned.

The published repository excludes raw data, every event-level prediction CSV,
input manifests, local caches/environments and execution logs. It includes locally
authored code, formulas, model parameters, aggregate research statistics and
figures. Machine-specific metadata paths are redacted in the public copy; numeric
model/evaluation/protocol evidence and their protected source hashes are unchanged.
The original local archive is retained separately. Public aggregate checks cannot
recreate ranking AUC or source-data quality without the private row/input evidence.

Historical hash/replay statements refer to their recorded experiment versions,
not to byte-identical publication of redacted machine metadata. PUBLICATION.md
records the publication scope and fresh-environment verification. The final
Holdout is consumed and no execution profitability is established.
