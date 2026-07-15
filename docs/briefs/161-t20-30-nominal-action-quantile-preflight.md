# Slice Brief 161 - T20.30 Nominal-Action-Quantile Preflight

**Date:** 2026-07-14

## Objective

Materialize and centrally authorize the exact recovery-training dataset view
whose only statistics change is replacing action q01/q99 with the clean nominal
values, without loading a model or running an optimizer.

## Contract

- Bind the verified T20.23 recovery dataset/specification and T20.29
  counterfactual. Preserve every data, episode, task, and info byte exactly.
- Create a distinct persistent dataset root. Replace only `action.q01` and
  `action.q99` in `meta/stats.json`; every other statistic remains recovery
  derived. Reject aliases, mutation of the source root, or any other drift.
- Verify the actual package dataset still exposes 10 episodes and 2,330 frames.
- Freeze the future campaign to the same clean base, dataset membership,
  sampler seed 20260714, batch size one, rank-4 LoRA, local MPS, and 500 updates.
- Compose a fresh central decision that may grant only
  `simulation_training_ready`. T20.30 itself keeps all execution fields false.
- Do not load a model, run inference/training/rollout, access hardware/cameras,
  start external compute or Brev, or grant policy/transfer/promotion authority.

## Acceptance Criteria

- Tests reject source or non-action-stat drift, partial/extra replacement,
  non-finite/zero-span quantiles, path aliasing, cardinality drift, signed
  mutation, campaign drift, and authority escalation.
- A signed manifest and training specification reconstruct from live sources.
- Central authority recomposes to only `simulation_training_ready`.
- Focused and broad tests, same-agent review, canonical state, ledger, plan,
  session log, reviewer decision, scoped commits, and remote preservation agree.

## Out Of Scope

Model load; optimizer; checkpoint; evaluation; policy acceptance; hardware;
camera; twin change; Robo Scan; physical transfer; external compute; or Brev.
