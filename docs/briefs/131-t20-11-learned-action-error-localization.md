# Slice Brief 131 - T20.11 Learned-Action Error Localization

**Date:** 2026-07-14

## Objective

Localize the earliest and largest requested-action errors for the four T20.7
checkpoints against the exact seed-2 source oracle before selecting another
training hypothesis.

## Contract

- Re-hash and load the same PI0.5, SmolVLA, ACT, and Diffusion checkpoints from
  the verified T20.7 equal-sample run; run no optimizer step.
- Evaluate each model from the same seed-2 reset through the corrected T20.10
  force-bearing release semantics, with the same 244-frame schedule, action
  horizon 5, five 256 px keyframes, projection accounting, and strict margins.
- Compare every requested model action to the immutable source action at the
  same frame, reporting first divergence, per-phase/per-joint MAE and maximum
  error, initial identical-reset error, and gripper-specific error. Preserve
  requested actions before clipping.
- Label frame-0 error as an identical-observation prediction error. Label later
  closed-loop errors as prediction plus compounding state-distribution drift;
  do not misstate them as teacher-forced loss.

## Acceptance Criteria

- All four model/checkpoint/source identities verify and all 244 finite action
  comparisons are accounted for per model.
- A signed comparison gate reports measured errors and the earliest divergent
  joint/frame for each model without using cross-model loss scales as ranking.
- Tests reject action reordering, missing frames/phases/joints, non-finite
  values, source substitution, projection omission, model-result swapping, and
  authority escalation.
- Same-agent review checks coordinate representation, horizon queues, initial
  reset equality, clipped-versus-requested confusion, and false capability
  claims.

## Out Of Scope

Optimizer training, architecture or dataset mutation, policy acceptance,
residual RL, hardware, physical transfer, promotion, external compute, and
Brev.
