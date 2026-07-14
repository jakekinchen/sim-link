# Executor Session 148 - T18.1 Episode-First Window Sampling

**Date:** 2026-07-13

## Slice

Implemented T18.1 as a deterministic, selection-only M18 view over verified
M17 windows. It selects one valid window per realized episode in each complete
source-class/task-phase/control-mode/horizon bucket. It does not persist a
buffer, freeze a mixture, load a model, or open training.

## Evidence

- The signed manifest has 24 complete buckets and 8 realized source episodes.
  Each bucket selects exactly one hash-ranked window per episode, producing 192
  unique windows and a unique-window ratio of 1.0.
- The fixed seed is `181001`; source window index and T17.7 audit hashes are
  bound. Phase-spanning, ineligible, quarantined, discontinuous, timestamp
  drifting, or boundary-crossing windows are rejected before bucket selection.
- The tracked manifest identity is
  `17f804ddd463b70cba99431bbb7aac4183a0745beb4add0ab2e20832a252cdbc`.
  Its one sampling-cycle identifier is a logical selection boundary only;
  `buffer_persisted` and `buffer_mutated` remain false.

## Validation

- Four focused sampling tests and the 83-test relevant regression set passed.
  Tests reject duplicate IDs, episode shortfall, phase ambiguity, audit/authority
  drift, and raw rewrite attempts.
- The writer regenerated the 192-window selection byte-for-byte. T17.7 source
  bindings were verified before selection.
- `git diff --check` and the project-state pointer guard passed. No raw store,
  normalization, model, optimizer, training, hardware, physical actuator,
  external compute, or Brev resource was touched.

## Review Focus

The sampler fails closed if a bucket lacks even one realized episode. It cannot
meet a quota by duplicating, padding, or substituting windows. This is sampling
proof only; T18.2 owns append-only buffers and the central training lock remains
closed.

## Next Suggested Slice

T18.2: define immutable logical source/cycle buffers with duplicate and prior
cycle mutation rejection over this verified selection.
