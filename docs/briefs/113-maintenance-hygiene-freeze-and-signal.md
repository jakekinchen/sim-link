# Slice Brief 113 - Maintenance Hygiene, Frozen Diagnostics, And Gate Signal

**Date:** 2026-07-13

## Objective

Reduce repeated verification cost around the completed T19 grasp diagnostics,
make missing optional dependencies fail as explicit collection skips, provide
one registry-driven writer for uniform artifacts, establish the content-
addressed evidence-image contract for future outputs, and move append-only
proof-state history out of `GOAL.md`.

This is a secondary offline maintenance slice. The active T17.5b implementation
and its dirty worktree evidence remain preserved; this slice does not grant
training, hardware, Brev, or physical authority.

## Contract

- Stored T19.0 diagnostic JSON remains signed and tracked. Its frozen registry
  checks schema, signed identity, and file SHA-256 without importing or running
  a historical builder.
- The current test collection path skips only modules whose local top-level
  import graph needs an unavailable optional package. Function-body imports do
  not cause a skip.
- Uniform single-artifact writers use lazy string bindings in one registry.
  Specialized wrappers with calibration, multi-file, runtime, or authority
  flags remain intact until a separately reviewed migration.
- New rendered evidence images are append-only bytes named by SHA-256 and
  referenced by a signed manifest. Existing embedded historical JSON is not
  rewritten.
- `GOAL.md` retains the active mission/window/milestone and points to the
  append-only proof-state history file.

## Verification

- Focused frozen-diagnostic and semantic test set passes in the available
  MuJoCo runtime.
- Evidence-image, optional-import, and writer-registry tests pass.
- Python compilation passes for all new and edited maintenance modules.
- Full pytest collection remains unavailable in this checkout because neither
  local virtualenv contains pytest; this is recorded as an environment limit,
  not a passing broad gate.

## Out Of Scope

No physical hardware, camera, serial port, optimizer training, Brev, external
compute, deletion of historical evidence, or modification of the active T17.5b
generator/output records.
