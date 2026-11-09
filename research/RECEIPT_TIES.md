# Receipt timestamp ambiguity hardening

This change is for new studies. It does not rescore or replace any published
experiment, model, scaler, threshold, protocol, metric or consumed holdout.

## Version and entry point

The recorded external protocol fingerprints `src/obi_research/features.py`.
That file and all historical research runners remain unchanged so their existing
source checks and replay semantics remain intact. The hardened implementation is
`src/obi_research/features_v2.py`, exposed as the package-level entry point:

```python
from obi_research import prepare
from obi_research.features import targets

grid, records, audit, session = prepare(rows, config)
labels = targets(grid, records, horizon=1)
```

Historical runners explicitly importing `obi_research.features.prepare` continue
to use frozen v1, including its known tie limitation. They are not silently
upgraded to v2. New studies must record the v2 source/version before inspecting
outcomes; changing preprocessing does not restore an unused holdout. The
publication-v1 file manifest remains the original release snapshot.

## Available ordering evidence

Inspection of the normalized BBO schema and the source collector found receipt
time, exchange time, session ID, payload hash, quote fields and displayed order
counts. There is no per-event exchange sequence or persisted monotonic receive
sequence. The payload contains `coin`, `time` and `bbo`; a level's `n` is an order
count, not a sequence number. Event IDs hash payload content and cannot order it.
Neither exchange timestamps nor physical file/row order establish a trustworthy
order among observations with identical receipt timestamps.

No collector code or private observations are included in this change. This
inspection does not establish what a future feed might provide. Additional
ordering fields require a separately validated contract before being used.

## Conservative policy

1. Retain the existing session-selection rule and sort by receipt time only.
2. Validate every row's source, payload identity, exchange time and normalized
   quote values, including rows whose event IDs were previously seen.
3. Collapse identical validated event IDs. Repeated deliveries retain the earliest
   receipt and cannot refresh a quote or resolve an ambiguous state.
4. A receipt group containing multiple distinct validated event IDs and new
   information is ambiguous. Invalidate the whole group even if its predictor
   values match, or only one candidate would otherwise pass quality checks.
   An all-duplicate replay group adds no new state.
5. Do not select a winner using prices, quantities, hashes, exchange timestamps
   or row order. Compare exchange reversals only against earlier receipt groups.
   Carry the group's maximum observed exchange time solely as a conservative
   high-water mark for later reversal checks, never as a selected quote.
6. The ambiguous state remains unavailable until a subsequent unambiguous,
   admissible new event. Do not fall back to an older valid quote. Existing
   receipt-age and lag limits still apply.

`ambiguous_receipt_groups` counts ambiguous groups;
`duplicate_receipt_timestamp` counts additional distinct events in such groups;
`duplicate_event_id` counts repeated deliveries. These distinguish ambiguity
from duplication. An isolated single-event series has no interval quantiles.

The shared target generator rejects a label if any grid state from its start
through its endpoint is invalid. Tests cover ambiguity at endpoints and inside
future-label windows, delayed recovery, exact duplicates, tampered duplicates,
exchange reversals and every permutation of six-row synthetic inputs. Features,
validity masks, audit counts and labeled populations must all be invariant.

## Limits and public verification

This policy can discard usable observations because their order is unknowable.
An extreme exchange timestamp can also keep subsequent observations below the
high-water mark; there is no inferred clock repair. Validity concerns sampled
grid states and does not certify loss-free feed coverage or synchronized clocks.

The recorded inventory reports zero receipt ties and zero duplicate events.
The synthetic failure is not evidence that historical metrics were affected.
No published numeric artifacts were rewritten or selected using new outcomes.

The workflow **Public code and aggregate verification** installs the public
package on Python 3.11, runs all tests, verifies published aggregates and hashes,
checks dependencies and checks for rewritten tracked files. It uses no private
data, credentials, fitting, collection or holdout-consumption commands. This is
public verification, not full historical research reproduction. A hosted result
is available only after the reviewed workflow reaches GitHub; local execution of
its commands does not establish that a hosted run has succeeded.
