# Temporal-role correction — after registered robustness evaluation

The immutable external-v1 protocol listed every non-pilot/non-reserved session
for robustness. A temporal review after the registered scores identified that
`f1d0c0b3bd1f4c7b844074508477be4c` ended at2026-10-07 05:15:40 UTC, before
the original training interval started. Its325 quotes were not used to fit the
models, but its predictions cannot represent a model available at that earlier
time. It was also part of the previously inventoried first-hour input files.

This is a temporal-role design correction, not a change selected to improve
performance. The original registered result remains in `results/oos/robustness.json`.
The retrospective session is disclosed separately. No original-model coefficients,
filters, hyperparameters, thresholds or primary independent-session result change.
Its1s BA was1.000 on only7 directional observations, so removing it is not hiding
a bad session.

The separate chronological aggregate includes only sessions starting strictly
after the entire original session ended at2026-10-07 07:44:11.358403 UTC;
the original session and the latest reserved session remain excluded. This
leaves25 prospective temporal-role sessions,549,246 raw BBO and66,679 valid
one-second feature states. The first external16,945-quote session is unaffected.
The exact cutoff, excluded ID, original-result hash, frozen-model hash and
correction-script hash are saved before computing corrected aggregate results
in `results/oos/chronology_addendum.json`.

`research/chronological_robustness.py` computes the corrected aggregates with the
same frozen helpers and no fit(). Reports distinguish this post-protocol correction
from the original local pre-evaluation protocol. Results after this audit are
seen data; no further rule or model search may be called confirmatory. The latest
reserved session remains unused for returns and prediction scores.
