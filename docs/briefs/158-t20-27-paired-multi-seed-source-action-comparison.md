# Slice Brief 158 - T20.27 Paired Multi-Seed Source-Action Comparison

**Date:** 2026-07-14

## Objective

Measure the clean-versus-recovery training difference at one identical
frame-zero observation by pairing their T20.26 actions over the same inference
seeds and comparing each pair with the exact source action.

## Contract

- Run no model and no optimizer. Reverify the four T20.26 batch artifacts, the
  exact held-out seed-6 source episode, both checkpoints, and the T20.26 gate.
- Require each candidate's two independent process batches to reproduce every
  scheduled action exactly before selecting one duplicate-free paired view.
- For the shared baseline seed and four shared distinct seeds, report clean and
  recovery source-relative MAE, recovery-minus-clean delta, candidate-to-
  candidate difference, per-joint errors, and improved/regressed/tied counts.
- Keep the conclusion bounded to frame-zero requested-action distribution.
  Do not infer closed-loop contact, strict success, or optimizer value.
- Do not access hardware or cameras, apply an action, run inference/training,
  start external compute or Brev, change the twin, or consume Robo Scan evidence.

## Acceptance Criteria

- Tests reject source substitution, batch/candidate/seed/sample/joint reorder,
  duplicate-process disagreement, non-finite actions, signed mutation, and
  authority escalation.
- A signed gate accounts for five unique paired inference seeds and all six
  joints, records distribution-level source error, and makes no significance
  or closed-loop capability claim.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commits, and
  remote branch agree before T20.27 is described as verified.

## Out Of Scope

Model inference; rollout; optimizer training; checkpoint/dataset/statistics
changes; policy ranking or acceptance; physical canary; hardware/camera access;
twin calibration; Robo Scan; external compute; or Brev.
