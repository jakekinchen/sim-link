# Slice Brief 164 - T20.33 Gate B One-Batch Memorization

**Date:** 2026-07-14

**State:** `in_progress`

**Pre-run implementation boundary:** `38fa450`

**Pre-run reviewer decision:** `194`

**Training-spec identity:**
`3fa3098c816b228a6687e952cb8444c77344e49877b17cfc5d1afdc32e6e685a`

**Central authority identity:**
`ff3ac3c99eb71f4774976f02c8ae7d3d17827451f4c738c2ceaddf3545db5348`

## Objective

Prove or falsify the lowest unmet policy-capability gate routed by T20.32:
whether the current official PI0.5 LoRA model/trainer/inference plumbing can
memorize one exact source batch to a declared near-zero action-error boundary.

## Contract

- Bind one fixed batch only: T20.17 source-native dataset, training episode 0,
  frame 0, with its exact horizon-50 measured-action target, top/wrist images,
  state, task, dataset statistics, coordinate conversion, base snapshot, and
  processor identities. No sampler may substitute another frame.
- Start from the pinned clean `lerobot/pi05_base` snapshot, use the official
  dataset-statistics pre/postprocessing path, rank-4 LoRA, local MPS float32,
  batch size one, fixed learning rate, fixed seeds, and exactly 500 optimizer
  updates on that same batch. No retry, sweep, second batch, or continuation.
- Before model load or optimizer creation, produce a signed training
  specification, owner-scope grant, central-composer request, and central
  `simulation_training_ready` decision. Their implementation, deterministic
  tests, same-agent pre-run review, project state, scoped commit, remote branch,
  and runtime validity must agree.
- Record every finite objective value and gradient norm, the adapter tree, and
  five fixed-seed post-training decoded horizon-50 action chunks. Compare each
  complete chunk against the exact measured source target in MuJoCo radians.
- Gate B passes only if all five decoded chunks have maximum absolute error at
  most 0.05 rad and the final five-seed mean training objective is no greater
  than 10 percent of its baseline. Otherwise record a verified negative and
  keep Gate C and further campaigns closed.
- No closed-loop rollout, dataset/statistics/twin mutation, hardware, camera,
  Robo Scan artifact, external compute, Brev, policy acceptance, transfer, or
  promotion.

## Acceptance Criteria

- Deterministic tests reject source/batch/index/horizon/update/threshold/seed,
  non-finite, authority, and result mutation before execution.
- The pre-run authority is centrally composed, training-only, current, reviewed,
  committed, pushed, and remotely confirmed before the optimizer starts.
- The immutable result binds exact batch, runtime, checkpoint, loss/gradient,
  and decoded-action evidence and makes exactly one Gate B pass/fail decision.
- Focused and relevant broad tests, same-agent adversarial review, state,
  ledger, plan, session log, reviewer decisions, scoped commits, and remote
  preservation agree before T20.33 is verified.

## Out Of Scope

Gate C chunk/cadence/feedback changes; training or evaluation on any second
batch; hyperparameter search; full-dataset or held-out campaign; closed-loop
rollout; promotion; hardware; external compute; Brev; or global authority
change.
