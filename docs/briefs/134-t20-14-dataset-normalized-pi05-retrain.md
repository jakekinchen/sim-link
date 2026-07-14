# Slice Brief 134 - T20.14 Dataset-Normalized PI0.5 Retrain

**Date:** 2026-07-14

## Objective

Falsify the T20.13 preprocessing hypothesis with one bounded local-MPS PI0.5
LoRA retrain using frozen train-only statistics and a fixed seed-2 strict
closed-loop evaluation.

## Contract

- Re-hash T20.1, T20.7, and T20.13 sources; require live simulation-training
  authority immediately before model load and optimizer execution.
- Use the exact T20.7 ordered 20-sample schedule, rank-4 LoRA, seed, optimizer,
  task prompt, images, and action horizon. The only intended intervention is
  T20.13 train-only state/action statistics; keep all six loss weights 1.0.
- Record baseline/final aggregate and per-dimension train/held-out losses,
  finite gradients, realized samples, checkpoint hashes, and the exact
  effective normalizer.
- Evaluate the resulting checkpoint from the same seed-2 reset under T20.10
  force-bearing release semantics with 244 policy-owned frames, five 256 px
  keyframes, requested-action tracing, projection accounting, and every strict
  measured-versus-threshold margin.

## Acceptance Criteria

- Exactly 20 finite optimizer updates use the common schedule with no sample,
  loss-weight, dataset, source-checkpoint, or authority drift.
- The fixed rollout is source-bound, deterministic on rerun, and reports the
  first requested-action divergence plus strict behavior without assistance.
- Tests and same-agent review reject normalizer fallback, held-out leakage,
  missing per-dimension loss, checkpoint/result swaps, action clipping
  omission, false capability claims, and authority escalation.
- A negative result remains verified evidence and selects at most one narrow
  next hypothesis; no policy is accepted without strict semantic success.

## Out Of Scope

More than 20 optimizer updates, loss reweighting, model-family changes,
hardware, physical transfer, promotion, external compute, and Brev.
