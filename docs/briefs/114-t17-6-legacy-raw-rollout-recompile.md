# Slice Brief 114 - T17.6 Legacy Raw-Rollout Recompile

**Date:** 2026-07-13

## Objective

Inventory the bounded local legacy canary evidence already present in this
checkout. Recompile only records that already meet the current T17.1 raw
rollout/frame contract; retain a signed, reasoned quarantine for every other
candidate without guessing missing action, image, coordinate, provenance, or
temporal semantics.

## Contract

- Inspect only the configured local legacy-canary roots identified by the new
  task writer. Do not scan user home directories, external checkouts, network
  sources, hardware, or ignored data beyond those explicit paths.
- A candidate is eligible only if its raw rollout and frames validate against
  the current signed experience-record contract exactly: six finite named
  action values and truthful state/provenance, integer strictly increasing
  timestamps, complete hard boundaries, source/twin/coordinate identities, and
  actor-input declarations. No field may be synthesized, transformed, renamed,
  padded, or reordered.
- Retain immutable file hashes, candidate path, discovered schema/source class,
  accepted/rejected outcome, and deterministic quarantine reason codes in a
  tracked manifest. Raw legacy bytes remain untouched and ignored when they
  are not already tracked.
- Compile accepted records through the existing source-bound compiler into a
  new output view. Emit an explicit empty view when no candidate qualifies;
  accepted legacy rows must never bridge records or hard boundaries.
- This is an offline forensic pass only. It must not alter T17.5b raw evidence,
  normalization, mixture, training lock, optimizer, Brev, external compute,
  hardware, or physical authority.

## Acceptance Criteria

- Re-running the fixed inventory produces byte-identical manifest and compiler
  output. Every candidate has either exact validation evidence or at least one
  precise quarantine code.
- Tests reject root escape, source/hash drift, duplicate candidates, malformed
  records, unknown action semantics, missing provenance, timestamp/boundary
  ambiguity, authority escalation, and any attempted raw rewrite.
- The manifest states configured/discovered/accepted/quarantined counts and
  preserves truthful zero acceptance if the legacy canary cannot meet the
  current contract.

## Out Of Scope

No migration inference, data repair, action conversion, dataset mixture,
optimizer or policy training, hardware, physical motion, Brev, external
compute, or deletion.

## Stop Conditions

Stop and quarantine if a candidate needs any inferred field or source rewrite,
if its hash/path cannot be bound, or if the fixed inventory root is absent.
Do not expand the search root without a separately reviewed brief.
