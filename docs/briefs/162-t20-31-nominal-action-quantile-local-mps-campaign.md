# Slice Brief 162 - T20.31 Nominal-Action-Quantile Local-MPS Campaign

**Date:** 2026-07-14

## Objective

Run the exact centrally authorized T20.30 quantile ablation for 500 local-MPS
updates, then evaluate the frozen adapter unassisted on held-out seeds 6 and 7.

## Contract

- Reverify T20.30 dataset, spec, clean base, and active central decision before
  creating the run root or loading a model.
- Use official LeRobot, rank-4 LoRA, batch size one, seed 20260714, offline
  local MPS, and exactly 500 updates. Record every finite loss and checkpoint.
- Freeze the adapter, then evaluate seeds 6 and 7 once each with inference seeds
  20260714/20260715, horizon 5, no projection, assistance, or fallback.
- Record exact strict-v2 results and rendered keyframes. Keep policy acceptance,
  transfer, and promotion false regardless of outcome.
- Do not access hardware/cameras, start external compute or Brev, or change the
  twin or source datasets.

## Acceptance Criteria

- Tests reject argv/update/loss/checkpoint/seed/assist/authority drift.
- Training completes 500 finite updates and emits a reloadable bound adapter.
- Both 244-frame held-out evaluations complete with signed strict-v2 evidence.
- A signed result gate records the honest outcome without promotion.
- Focused/broad tests, same-agent review, state, ledger, plan, logs, commits, and
  remote preservation agree before T20.31 is verified.

## Out Of Scope

Additional training, hyperparameter sweep, policy promotion, physical canary,
hardware/camera, twin update, Robo Scan, external compute, or Brev.
