# Session 319 - T20.43c Manual Replacement Implementation

**Date:** 2026-07-16
**Task:** T20.43c-R2 / Brief 229
**Reviewer:** 315

## Outcome

Implemented and reviewed one disjoint manual ACT replacement after preserving
the consumed T20.43c continuation. The implementation never claims an exact
resume from update 728: it starts from the same checkpoint-0 tensors only after
bit-exact fresh-seed equivalence, empty AdamW state, and zero consumed batches.

The runner keeps the original seed, R0 dataset, optimizer, 10,000-update
schedule, checkpoint cadence, and dual-semantics strict-v2 evaluation. New
authority, marker, result, and run-root paths prevent reuse or coexistence with
the first continuation. A four-hour completion-budget check precedes the
marker, and any marked failure authorizes no retry.

## Verification

- 7 focused tests pass.
- 67 selected tests plus 15 subtests pass in 76.85 seconds.
- Ruff lint and format pass; compilation and whitespace checks pass.
- Prior terminal identity `d848a1a8...`, update count 728, and 14-file partial
  tree reconstruct against local retained evidence.
- Model-free central preview grants only `simulation_training_ready`.

No R2 authority artifact, acceptance, marker, checkpoint tensor read, model,
optimizer, rollout, Gate C action, hardware, network, external compute, or Brev
action occurred. Training remains locked pending origin preservation and a
separate authority materialization/review boundary.
