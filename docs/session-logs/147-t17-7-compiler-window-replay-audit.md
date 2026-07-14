# Executor Session 147 - T17.7 Compiler Window Replay Audit

**Date:** 2026-07-13

## Slice

Implemented T17.7: a deterministic, read-only audit of the verified T17.5b
grasp source. The signed audit follows selected windows through append-only raw
frame records, compiler rows, segments, and unpadded index rows; it uses only
canonical input/action descriptors and never loads or calls a policy.

## Evidence

- The audit selects exactly 100 windows: 25 at each horizon 5/10/15/50. Every
  one of the eight realized scripted grasp rollouts appears in every horizon
  stratum before the remaining selections are hash-ranked.
- It binds 1,952 raw frames to 1,952 compiler frames, 88 segments, and 3,744
  index rows. Every selected window has contiguous frame indices, strictly
  increasing timestamps, no internal hard boundary, complete action variants,
  and matching raw-rollout identities.
- The tracked audit identity is
  `e0fca4fe23b184e61f90711818192df6a66fdf4e8219ea1feb9be73f12ba1caf`.
  It stores only identifiers, shapes, dtypes, and hashes; no raw image payload
  or raw action array is copied into the tracked result.

## Validation

- Five focused audit tests and the 79-test relevant regression set passed.
  Tests reject selection duplication/skew, raw/compiler identity drift,
  rollout-identity drift, internal boundary crossing, actor-input leakage,
  image hash drift, authority escalation, and raw-rewrite attempts.
- The writer reproduced the signed 100-window manifest byte-for-byte. Existing
  T17.4/T17.5b/T17.6 source writers remained verified.
- `git diff --check` and the project-state pointer guard passed. No model was
  loaded, no inference or optimizer ran, and no hardware, physical actuation,
  Brev, external compute, or raw rewrite occurred.

## Review Focus

Collection/training/inference parity refers only to canonical shared actor-input
descriptors, not model tensors or model execution. Requested actions remain a
separate descriptor for a later training target. This slice closes M17's data
integrity gate; it does not open the training lock.

## Next Suggested Slice

T18.1: sample the verified windows episode-first with deterministic source,
task-phase, and control-mode composition accounting.
