# Slice Brief 163 - T20.32 Closed-Loop Divergence Localization

**Date:** 2026-07-14

## Objective

Localize where and how the frozen T20.24 and T20.31 adapters first diverge
from the exact source trajectories in closed loop, using complete per-frame
traces and one bounded training-seed reproduction probe, with no additional
training.

## Context

T20.31 improved frame-zero expert-action MAE on both held-out seeds
(0.58653 to 0.46420 rad on seed 6; 0.65091 to 0.54575 rad on seed 7) yet ended
farther from the expert at every retained phase landmark, and both adapters
leave the anchor within 1.7e-12 m of identical non-contact positions. The
leading hypothesis is therefore closed-loop divergence during action-chunk
execution or observation feedback, not quantile statistics. The earlier T20.2
ACT control also failed closed loop with near-zero lift, which is consistent
with an execution-semantics or compounding-drift fault rather than a
PI0.5-specific one.

## Contract

- Reuse the verified T20.25 trace-capture machinery. For each adapter
  (T20.24, T20.31) and each held-out seed (6, 7), capture all 244 per-frame
  requested actions, postprocessed applied actions, joint states, and visited
  simulator states under the exact frozen evaluation configuration.
- Compute earliest-divergence localization against the exact source
  trajectory: first frame exceeding declared action-space and state-space
  thresholds, per-joint divergence onset, and divergence class
  (frame-zero prediction, pre-contact drift, action-chunk boundary,
  observation-feedback compounding).
- Run exactly one additional bounded, deterministic, unassisted closed-loop
  rollout per adapter on one training seed (seed 0) with a fixed inference
  seed, capturing the same traces. This tests closed-loop reproduction of a
  memorized trajectory (ladder Gate C) and separates dataset-coverage faults
  from execution-semantics faults. Inference only; no optimizer.
- Compare divergence structure across held-out and training seeds and against
  the open-loop frame-zero evidence from T20.26/T20.27. Record the routed
  hypothesis for the next ladder gate.
- Sign and content-address every trace, threshold, localization result, and
  comparison artifact. A negative or ambiguous outcome is recorded honestly.
- Use no optimizer, dataset mutation, statistics change, twin change,
  hardware, camera, Robo Scan artifact, external compute, or Brev API. Policy
  acceptance, transfer, and promotion remain false regardless of outcome.

## Acceptance Criteria

- Deterministic tests reject trace-shape, threshold, seed, adapter-identity,
  assistance, and authority drift before any rollout.
- All four held-out trace bundles and both training-seed probe bundles are
  complete, signed, and replay-consistent with their frozen evaluation
  identities.
- One signed localization report binds, per adapter and seed: first divergent
  frame, divergence class, per-joint onset, gripper-versus-arm attribution,
  and the training-seed reproduction outcome.
- The report routes exactly one next-gate hypothesis (memorization/plumbing,
  action-chunk execution semantics, observation feedback, or dataset
  coverage) with its supporting evidence identities.
- Focused/broad tests, same-agent adversarial review, state, ledger, plan,
  session log, reviewer decision, scoped commits, and remote preservation
  agree before T20.32 is verified.

## Out Of Scope

Any optimizer or training run; hyperparameter or dataset changes; new
robustness-grid cells; policy promotion; hardware, camera, or physical
calibration; Robo Scan consumption; external compute; Brev; or any global
authority change.
