# Slice Brief 132 - T20.12 PI0.5 Gripper-Channel Audit

**Date:** 2026-07-14

## Objective

Audit the PI0.5 gripper target end to end, from immutable MuJoCo source action
through LeRobot coordinates, tensor preprocessing, model normalization and
loss, and inference postprocessing, before selecting another optimizer
hypothesis.

## Contract

- Re-hash and load the exact T20.1 dataset/tensor contract and T20.7 PI0.5
  checkpoint evidence; run no optimizer step and mutate no dataset or model.
- Trace the seed-2 frame-0 source action and the complete train/held-out
  gripper distributions through every implemented conversion boundary. Report
  native units, transformed values, and exact inverse-round-trip errors.
- Reproduce the PI0.5 preprocessing and loss inputs without updating weights.
  Report per-joint target range, standard deviation, normalized scale, and
  loss contribution or weighting on a directly comparable basis.
- Trace the frozen frame-0 PI0.5 prediction through postprocessing back to the
  requested MuJoCo action and reconcile it with T20.11's 0.75432 rad gripper
  error.

## Acceptance Criteria

- A signed audit artifact binds every source, dataset, checkpoint, processor,
  and code identity needed to reproduce the trace.
- Every conversion and inverse conversion reports measured-versus-threshold
  round-trip margins; non-finite values, unit/sign inversion, clipping, or
  unsupported implicit defaults fail closed.
- The artifact distinguishes representation semantics from statistical or
  optimization weighting and names at most one evidence-supported next
  hypothesis, without claiming capability or model promotion.
- Deterministic tests reject source/checkpoint substitution, action reordering,
  missing gripper metadata, non-finite statistics, false round-trip claims,
  omitted loss accounting, and authority escalation.
- Same-agent review checks train/held-out leakage, coordinate aliases,
  normalized-versus-native confusion, requested-versus-clipped confusion, and
  unsupported causal claims.

## Out Of Scope

Optimizer training, checkpoint mutation, dataset mutation, policy acceptance,
residual RL, hardware, physical transfer, promotion, external compute, and
Brev.
