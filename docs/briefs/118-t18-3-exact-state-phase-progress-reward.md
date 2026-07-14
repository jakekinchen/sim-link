# Slice Brief 118 - T18.3 Exact-State Phase, Progress, And Reward Components

**Date:** 2026-07-13

## Objective

Compile exact-state phase, progress, and reward-component records with explicit
source provenance for the immutable T18.2 logical cycle. Preserve the actor
input boundary: privileged reward/progress/contact/strict-evaluator fields must
remain unavailable to an actor.

## Contract

- Consume only the verified T18.2 cycle registry, T18.1 selection, and bound
  T17.5b compiler frames. Verify source signatures/hashes/closed authority and
  exact cycle window membership before compiling any component.
- For every selected frame, retain source phase and exact signed frame identity;
  compile progress and reward from the existing sourced/derived frame fields
  without interpolation, relabeling, rounding, averaging, or inferred values.
- Each component must carry source frame identity, source pointer/provenance,
  availability state, units where applicable, and a deterministic exact-state
  predicate. Reject missing, non-finite, inconsistent, or unprovenanced values.
- Explicitly define the actor input schema as the four existing observation and
  joint fields only. Reward, progress, contact geometry, strict evaluator,
  aperture, effort, and all derived outcome fields are privileged and excluded.
- Keep buffer, mixture, model, inference, optimizer, training, raw rewrite,
  physical, external-compute, and Brev authority false.

## Acceptance Criteria

- Rerun is byte-identical. Every logical-cycle window/frame maps to a complete
  exact-state record with a source identity and no actor-input privilege leak.
- Tests reject source/cycle/hash drift, missing/non-finite/provenance fields,
  phase mismatch, duplicate frame records, privilege leakage, authority
  escalation, raw rewrite, and buffer mutation.

## Out Of Scope

No correction branch, mixture freeze, model load/inference, training/optimizer,
hardware, physical motion, Brev, external compute, or deletion.
