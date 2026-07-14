# Slice Brief 160 - T20.29 Quantile-Postprocessor Counterfactual

**Date:** 2026-07-14

## Objective

Measure whether the recovery-mixture action quantiles alone account for the
T20.27 frame-zero regression by cross-decoding the same normalized candidate
outputs under clean and recovery postprocessor statistics.

## Contract

- Run no model and no optimizer. Bind the exact clean/recovery `stats.json`,
  checkpoint postprocessor configs, package QUANTILES formula source, coordinate
  contract, T20.26 paired actions, T20.27 source action, and five seed pairs.
- For each candidate action, invert its own q01/q99 postprocessor to recover the
  normalized output, then decode that identical normalized vector under the
  other dataset's q01/q99. Report round-trip error and any coordinate clipping.
- Compare actual and counterfactual source-action MAE per seed/joint and the
  observed T20.27 recovery-minus-clean delta. Keep normalized model outputs
  fixed; do not call the result a full model/training ablation.
- Select or reject nominal-statistics freezing as the next bounded training
  hypothesis without opening an optimizer.
- Do not access hardware or cameras, apply an action, run inference/training,
  start external compute or Brev, change the twin, or consume Robo Scan evidence.

## Acceptance Criteria

- Tests reject stats/formula/source/candidate/seed/joint substitution,
  zero/non-finite quantile spans, round-trip error, hidden clipping, signed
  mutation, and authority escalation.
- A signed gate accounts for all five paired seeds and reports both directional
  stat swaps plus the gap from the observed T20.27 regression.
- The conclusion is bounded to postprocessor-only counterfactual evidence and
  grants no optimizer or policy authority.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commits, and
  remote branch agree before T20.29 is described as verified.

## Out Of Scope

State-preprocessor swap; model inference; rollout; optimizer training;
checkpoint/dataset/statistics mutation; full causal training ablation; policy
acceptance; physical canary; hardware/camera access; twin calibration; Robo
Scan; external compute; or Brev.
