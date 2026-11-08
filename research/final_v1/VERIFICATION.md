# Verification — final-v1,2026-11-08

The analysis is versioned under `research/final_v1/` and `results/final_v1/`.
Earlier numerical outputs and frozen evaluation sources remain unchanged. The
previous README is preserved verbatim in README_before_final.txt.

## Before final disclosure

- Reviewed the prior frozen model/protocol and preserved final role. Final session:
  `df37f36553464010ae9c34cd83d0eeac`,77,143 BBO. Prior inspections were quality-only.
- Registered a separate protocol before scoring: Primary A retained the original
  estimator/target/threshold/filters; B, policy band, coverage, training-only
  magnitude bins, cost scenarios and deferred markouts were fixed separately.
- Protocol SHA-256: `332f92af1d6274e3010a4858e6fd73fef100a59b90ca650d7899c1d50e49950e`.
  Model SHA-256: `a113817a95b9eee78df3f9a864b15e02217e2d2d4460fe0ecc7334087d5bdb20`.
- Original coefficients/scalers were loaded, not re-estimated. The registered
  runner has no model fit and disables LogisticRegression.fit at runtime.
- The consumption ledger was written before labeling and now records complete /
  seen_forever=true. A second first-disclosure call refuses before labeling.
  Explicit replay compares the consumed result and never marks it unused again.

## Calculation and reproducibility checks

- `python -m pytest -q tests`: **33 passed**, no skip (checked0.65s).
  `pip check`: **No broken requirements found**.
- Tests retain the original17 checks plus later external tests; final additions
  cover zero-return denominators, fixed abstention boundaries, quoted-gap
  comparison units, deferred benchmark timing, source/model/consumption hashes,
  Primary-versus-all-time metric identities and refusal of a second opening.
- Explicit Primary replay is byte-identical to primary_holdout.json. The fixed
  exploratory analysis, delay/summary records and all seven PNGs also reproduced
  byte-for-byte. All13 prereplay JSON/PNG hashes were preserved; protocol and
  consumption records did not change. See results/final_v1/reproduction.json.
- All69 pre-final source/research/result artifact hashes remain unchanged.
  The original LG book_features extraction is still byte-identical; existing
  model/source guards pass. No original LG/OMS files or raw input were written.
- The full3173-file input inventory is hash-checked before and after evaluation.
  `rebuild_manifest.py` checks the recorded archive fingerprint and only restores
  an ignored missing manifest, without rewriting numeric inventory or results.
- Current dependency versions and Python are recorded in environment.json;
  project-owned Python3.11 environment is used, not the original LG environment.
- A public-artifact project copy is checked without raw data, private Parquet
  predictions or ignored input manifests. Public tests can verify calculation
  contracts and aggregate consistency; full historical replay still needs data.
- The seven figures were inspected for sample size/unit/period labels, readable
  axes/legends and distinction between Primary, all-time agreement and markouts.
  Source ASTs and relative Markdown links are checked at completion.

## Scope

Primary1s BA is0.764 on4,184 nonzero outcomes, not76.4% unconditional decision
success. All-time forced agreement is0.456 on7,034 labels; its relation to
conditional Accuracy is explicitly tested. The one-second deferred sensitivity
changes benchmark/coverage and is not a measured execution latency experiment.
No PnL, real slippage, queue/fill probability, market impact or paid fee estimate
was generated. The final segment is on an already seen date, so onlytwo calendar
dates remain available. No collection, commit, push or raw-data upload occurred.

## Publication qualification

The release excludes private row-level CSVs, manifests and execution logs and
redacts machine metadata. Historical replay/count statements above describe the
local experiment. Fresh public-only installation, tests and the minimum example
are documented separately in PUBLICATION_VERIFICATION.md at the repository root.
Public aggregate tests cannot independently reconstruct AUC or raw-clock quality.
