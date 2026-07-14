# Executor Session 145 - T17.5b Scripted Grasp Episode Generation

**Date:** 2026-07-13

## Slice

Implemented T17.5b: deterministic recording of the verified geometry-derived
unassisted MuJoCo grasp into append-only raw episodes, then source-bound frame,
segment, and unpadded-window compilation.

## Evidence

- Eight fixed seeds completed as strict successes; Seed 0 retained the original
  strict 8/24/12/24 cycle plus 64 unassisted stable-hold recording frames.
- The ignored raw store has eight content-addressed episode files. Its tracked
  signed manifest identity is
  `3860158e201e457146a167cfa778da14f210d88fa223cb075a1ec6d422ecfd1a`.
- Seed 0 has five retained 256px top/wrist keyframes spanning pregrasp, close,
  grasp-hold, unsupported lift hold, and retreat.
- The fresh compiler view contains 1,952 eligible frames, 88 hard-boundary
  segments, and zero quarantines. Its unpadded index has 1,600/1,176/848/120
  rows at horizons 5/10/15/50.

## Validation

- 15 focused compiler/window/episode tests and a 68-test relevant regression
  set passed.
- Existing T17.4 compiler and T17.5 window writers passed `--verify` unchanged.
- The T17.5b writer regenerated all eight episodes into a temporary raw store
  and reproduced the stored signed manifest, compiler files, and window files
  byte-for-byte.
- `git diff --check` passed. No hardware, serial/camera access, training,
  optimizer, Brev, external compute, or physical actuation occurred.

## Review Focus

Derived variants are never relabeled as observed: each has a nonblank named
derivation, exact six-joint order, and finite values. Compiler and window
readers enforce those conditions independently. All hard boundaries remain
explicit, and every horizon-50 row lies entirely inside one stable-hold
segment. All authority flags remain false except local artifact-validity facts;
the central training lock remains closed.

## Next Suggested Slice

T17.6: recompile only qualifying legacy raw rollouts; retain reasoned quarantine
for any ambiguous record and do not infer missing evidence.
