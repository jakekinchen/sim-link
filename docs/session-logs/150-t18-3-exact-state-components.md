# Executor Session 150 - T18.3 Exact-State Components

**Date:** 2026-07-13

## Slice

Implemented T18.3 as a deterministic projection over T18.2 immutable logical
cycle `0001`, the signed T18.1 selection, and verified T17.5b compiler rows.
The result is an exact-state component manifest, not a materialized data buffer
or a training input.

## Evidence

- The signed manifest binds all 192 ordered logical-cycle windows to 1,345
  unique compiler-frame records. Every binding records the source frame ID,
  signed frame identity, and component-record identity.
- Each component preserves canonical task phase and source phase separately,
  preventing the established normalization cases from being misreported as a
  phase mismatch. Progress and reward retain their existing sourced/derived
  payloads, source pointers, source references, availability states, and
  finite deterministic predicates. Reward must equal the recorded strict
  evaluator binary result.
- Actor inputs are exactly `observation.top_rgb`, `observation.wrist_rgb`,
  `observation.joint_position`, and `observation.joint_velocity`. Reward,
  progress, contact geometry, strict evaluator results, gripper pose,
  aperture, effort, actions, and boundary events are explicitly privileged.
- The tracked manifest identity is
  `40f522d16b34bc4a854cb47d657d21ac71fc00fad562557c43016c15195d752a`;
  its file hash is
  `f907b2f6cac9c49dfe7e7f1bb5a72cf8819cc8220376e217ea5324ff5f3031a0`.

## Validation

- Four focused adversarial tests and the 90-test relevant regression set
  passed. They reject source/hash and logical-cycle drift, phase tampering,
  duplicate records, missing provenance, non-finite values, actor privilege
  leakage, authority escalation, raw rewrite, buffer mutation, and artifact
  rewrite attempts.
- The writer replayed byte-identically. `git diff --check` and the
  project-state pointer guard passed before the closure update.
- No model, inference, optimizer, training, raw rewrite, hardware, physical
  actuation, external compute, or Brev resource was used. The training lock
  remains closed.

## Review Focus

The record carries both task phase and source phase because phase normalization
is intentional in the compiler. The component artifact fails closed when an
immutable cycle differs from the signed selection or a source frame is absent,
ineligible, quarantined, or phase-inconsistent with its selected window.

## Next Suggested Slice

T18.4: implement snapshot branch-and-correct with immutable failure/correction
branches linked by `correction_event_id`; no training authority is implied.
