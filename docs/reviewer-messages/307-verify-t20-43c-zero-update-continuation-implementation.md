# Reviewer Decision 307 - Verify T20.43c Zero-Update Continuation Implementation

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43C_ZERO_UPDATE_CONTINUATION_IMPLEMENTATION_MODEL_FREE`

Brief 227's fail-closed continuation implementation is accepted for one
model-free authority materialization. This decision does not accept a marker,
checkpoint tensor read, model construction, optimizer, rollout, or Gate C run.

## Verified implementation boundary

- T20.43b's marker, terminal failure, checkpoint-0 tree/model, progress file,
  and chunk-50 trace remain in their original byte-exact run root. T20.43c
  writes all new output beneath
  `outputs/robot_lab/t20_43c_act_continuation_run_001`.
- The source loader reconstructs the complete signed T20.43b terminal boundary
  before accepting checkpoint identity `916200d0...`, model file
  `acc865fb...`, or trace identity `b707b815...`.
- The model-free preflight pins exact dependency versions, branch/source/origin,
  scoped implementation cleanliness, MPS, disk, output absence and alias state,
  source partial-tree identity, and an actual-T20.43b-schema v2 mirror smoke.
- The central composer must grant exactly `simulation_training_ready`; the
  separately named permit grants one continuation, forbids retry/replacement,
  and requires equivalence before update 1.
- After a future marker, the runner compares every saved checkpoint tensor to a
  fresh seed-20260801 ACT tensor with exact keys/shapes/dtypes/bytes, requires an
  empty AdamW state and zero consumed batches, then loads the identical state.
- The standard result remains a T20.43b recipe result, while a signed T20.43c
  outer receipt binds it to the original failure, source checkpoint/trace,
  continuation marker, equivalence receipt, and separate retention tree.

## Tests and adversarial review

Six new focused tests and the complete T20.43/T20.43b/T20.43c/T20.44 plus
central-composer selection pass: `57 passed, 15 subtests passed`. Compilation,
strict source-boundary verification, and whitespace checks pass.

Fresh review specifically rejected in-place mutation of the failed run tree,
unpinned dependencies, post-authority implementation drift, missing live-smoke
file verification, output path aliasing, scalar-tensor byte hashing failure,
authority escalation, and success/failure coexistence. Those cases now fail
closed. No non-finite acceptance path, graph ambiguity, double counting,
hardware/network/external/Brev grant, or destructive behavior was found.

## Disposition

Model-free T20.43c renderer smoke and compact authority materialization may run
only after this implementation boundary is committed and exact on origin. The
training lock remains closed. A second same-agent review and signed acceptance
must be preserved on origin before the sole continuation marker.
