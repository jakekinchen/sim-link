# Slice Brief 170 - T20.35d Decoded-Action Residual Localization

**Date:** 2026-07-15

**State:** `in_progress`

## Objective

Reproduce the five immutable T20.35c expert-only decoded-action hashes and
localize the remaining Gate B maximum-error residuals by seed, timestep, and
joint before selecting any correction.

## Contract

- Bind T20.35c specification `6c10a1c7...`, authority `75dc9c7d...`, attempt
  `43b2b721...`, run `9b1af8ee...`, checkpoint `439ae119...`, and result
  `f6f6b024...`.
- Reuse the same pinned base model, exact trainable-only checkpoint tensor set,
  source batch, dataset statistics, task, processors, horizon, and five
  inference seeds.
- Before inference, verify the checkpoint tree, signed tensor manifest,
  safetensors key set, shapes, dtypes, element counts, and PaliGemma-frozen
  expert-only parameter boundary.
- Run no optimizer and mutate no checkpoint. Deterministically decode exactly
  one horizon-50 chunk per frozen inference seed and require every chunk hash,
  mean error, and maximum error to reproduce T20.35c before localization.
- Retain each full decoded chunk, exact target chunk, absolute residual matrix,
  threshold-exceedance coordinates, and per-seed/per-joint/per-timestep
  summaries in one signed report.
- Distinguish joint-specific, chunk-boundary, and distributed residual
  concentration using predeclared deterministic counts; report the evidence
  even when no single concentration class dominates.
- No optimizer, additional training, closed-loop rollout, Gate C work,
  dataset/statistics/twin change, hardware, camera, external compute, Brev,
  policy acceptance, transfer, or promotion.

## Acceptance Criteria

- Deterministic tests reject source, checkpoint, tensor, seed, processor,
  decoded hash, metric, threshold, coordinate, non-finite, classification, and
  authority drift.
- A separately reviewed evaluation-only boundary is committed, pushed, and
  remotely confirmed before model construction or inference.
- All five T20.35c hashes and metrics reproduce exactly before residuals are
  interpreted.
- Focused and relevant broad tests, same-agent adversarial review, canonical
  state, ledger, session log, reviewer decisions, scoped commits, and remote
  preservation agree.

## Out Of Scope

Optimizer construction; training; checkpoint mutation; threshold relaxation;
new batch or seed; action correction; Gate C; campaign; rollout; hardware;
external compute; Brev; transfer; promotion; or global authority change.
