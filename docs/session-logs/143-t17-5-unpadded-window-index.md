# Executor Session 143 - T17.5 Unpadded Window Index

**Date:** 2026-07-13

## Slice

Implemented T17.5: deterministic source-bound compilation of unpadded action
window indexes at horizons 5, 10, 15, and 50 from verified T17.4 segments.

## Files Changed

- Added `experience_window_index.py`, its deterministic writer, focused tests,
  and the tracked empty-source output directory.
- Updated GOAL, canonical state, ledger, and Brief 111. Adopted the reviewed
  T17.5b proposal as the next pending task.

## Tests / Validation

- 6 focused window-index tests passed.
- 74 relevant compiler/contract/processor/normalization/pointer/authority
  tests passed.
- T17.4 and T17.5 writers both passed `--verify`; pointer and lock checks and
  `git diff --check` passed.

## Reachability

The tracked writer recompiles the current T17.4 output into a zero-row Parquet
index and verifies its hashes. The empty result is expected because T17.4 has
zero eligible segments; no padding or inferred action is introduced.

## Evidence

- `window_index.parquet`: `d03744b08fa52bc741ed52a57e0a09684aef604f4d945f0dc3a184b10560b091`
- `window_manifest.json`: `72be8a73257a7956491170f243befe7558095f76eecf1541f6941839fefb015b`
- All training, optimizer, physical, and raw-rewrite flags remain false.

## Step-9 Flags For Reviewer

- Source-manifest/hash, frame/segment identity, duplicate IDs, contiguity,
  timestamp gaps, action completeness/finiteness, hard boundaries, and output
  authority flags were adversarially reviewed.
- The proposed T17.5b recorder's `derived` action semantics conflict with the
  current observed-only compiler. It must be fixed truthfully before emitting
  any non-empty data; derived values may not be relabeled as observed.

## Next Suggested Slice

T17.5b: add the narrow fail-closed `derived` action compatibility rule, then
record the existing verified scripted grasp into append-only raw episodes.
