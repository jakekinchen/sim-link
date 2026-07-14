# Slice Brief 135 - T20.15 State/Action Normalizer Ablation

**Date:** 2026-07-14

## Objective

Isolate whether T20.14's broad frame-zero arm regression comes from changing
PI0.5 state-token preprocessing, action postprocessing, or their interaction.

## Contract

- Re-hash T20.10, T20.13, T20.14, the seed-2 source episode, and adapter before
  model load. Use only the T20.14 checkpoint and exact source frame-zero
  images, state, task, oracle action, model seed, and local-MPS runtime.
- Run four common-random-number inferences: checkpoint state/checkpoint action,
  checkpoint state/dataset action, dataset state/checkpoint action, and dataset
  state/dataset action. Reset the policy and inference RNG before every cell.
- Change only the selected state preprocessor and action postprocessor. Record
  canonical six-joint actions, per-joint oracle errors, arm/gripper summaries,
  processor identities, and pairwise deltas with measured margins.
- Execute no optimizer, rollout, projection, simulation stepping, hardware,
  external compute, or Brev.

## Acceptance Criteria

- All four cells use the same model, source observation, raw normalized model
  output under each repeated state condition, and deterministic inference seed.
- The result distinguishes state-only, action-only, and interaction effects;
  it selects at most one next hypothesis and does not claim closed-loop
  capability.
- Tests and same-agent review reject source/checkpoint swaps, hidden pipeline
  changes, stochastic-seed drift, joint-order errors, non-finite actions,
  optimizer execution, and authority escalation.

## Out Of Scope

Further training, multi-frame rollout, model-family changes, action clipping,
hardware, physical transfer, promotion, external compute, and Brev.
