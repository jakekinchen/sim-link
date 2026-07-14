# Slice Brief 119 - T18.4 Snapshot Branch-And-Correct

**Date:** 2026-07-13

## Objective

Implement immutable snapshot and branch-and-correct mechanics over the verified
T18.2 logical cycle and T18.3 exact-state component records. The current
scripted grasp source contains no truthful correction event, so the tracked
artifact must report zero realized corrections rather than manufacture failure
or correction evidence.

## Contract

- Verify the signed T18.3 manifest and its exact T18.2 logical-cycle binding
  before creating any snapshot. Every window snapshot retains window, frame,
  component-record, and signed source-frame identities sufficient for an exact
  restoration check.
- A correction event has one deterministic `correction_event_id` linking a
  distinct immutable failure branch and correction branch. A branch may refer
  only to registered snapshots; it must preserve its source snapshot identity
  and never overwrite a prior branch or event.
- The initial tracked manifest contains only source/base snapshots and zero
  correction events unless source-bound correction evidence is present. Fixture
  branch events are allowed only in tests and must not be emitted into tracked
  source evidence or counted as a realized correction.
- Rebuilding a snapshot from its source must be byte-identical. Restoring a
  registered snapshot must exactly recover its ordered frame/component identity
  sequence. Missing, duplicate, altered, cross-window, or cross-branch records
  must fail closed.
- Keep buffer, mixture, model, inference, optimizer, training, raw rewrite,
  physical, external-compute, and Brev authority false.

## Acceptance Criteria

- The initial source-bound manifest is byte-identical on rerun and truthfully
  reports zero correction events if none are present in the source.
- Tests cover exact snapshot restore, duplicate or altered snapshot rejection,
  invalid/missing event references, same-branch or reused-event rejection,
  fixture/source evidence separation, authority escalation, raw rewrite, and
  buffer mutation.

## Out Of Scope

No correction data collection, generated failure labeling, mixture freeze,
model load/inference, training/optimizer, hardware, physical motion, Brev,
external compute, or deletion.
