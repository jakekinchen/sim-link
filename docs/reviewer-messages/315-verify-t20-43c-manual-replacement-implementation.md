# Reviewer Decision 315 - Verify T20.43c Manual Replacement Implementation

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43C_R2_IMPLEMENTATION_AND_MODEL_FREE_MATERIALIZATION_ONLY`

The T20.43c-R2 implementation is fail-closed and separately rooted. It does
not reuse marker `e086c293...`, permit `166a6cd0...`, failure `d848a1a8...`, or
the first continuation run root.

## Evidence

- Implementation commits `75647da9...`, `da7ea6a1...`, and `d0e2b2b9...`
  preserve the prior terminal tree and add disjoint authority, marker, result,
  and local-output paths.
- Seven focused tests pass. The selected T20.43/T20.43b/T20.43c/R2,
  authority-composer, and pointer set passes 67 tests plus 15 subtests.
- Ruff lint/format, Python compilation, strict JSON, and whitespace checks pass.
- A model-free reconstruction verifies prior interruption `d848a1a8...` at
  update 728 and previews a central decision granting only
  `simulation_training_ready`.
- No R2 owner/request/decision/runtime/permit, acceptance, marker, checkpoint
  read, model, optimizer, rollout, or Gate C artifact exists.

## Adversarial findings

- Exact update-728 resume is impossible because optimizer state was not
  retained; the implementation labels the new process a manual replacement.
- The four-hour completion-budget gate runs before the marker.
- Materialization rejects absent, untracked, dirty, aliased, or non-origin
  implementation inputs.
- The first replacement marker and partial tree remain immutable and are
  re-verified before any R2 authority construction.
- Exceptions and keyboard interruption after the R2 marker produce a bounded
  signed terminal tree; no subsequent retry is authorized.
- The central composer rejects broader authority, while hardware, network,
  external compute, Brev, transfer, and promotion remain false.

## Authority granted

After this reviewed implementation boundary is exact on origin, materialize
one model-free T20.43c-R2 owner/request/decision/runtime/permit bundle within a
finite window. Preserve it for a separate pre-run review.

## Authority withheld

No acceptance, replacement marker, checkpoint tensor read, model construction,
optimizer creation/training, policy rollout, Gate C execution, retry after the
new marker, recipe/data/schedule/threshold change, hardware, camera, serial,
physical motion, network, package installation, external compute, Brev,
transfer, promotion, or destructive operation.
