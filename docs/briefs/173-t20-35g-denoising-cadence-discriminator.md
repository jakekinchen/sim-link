# Slice Brief 173 - T20.35g Denoising Cadence Discriminator

**Date:** 2026-07-15

**State:** `in_progress`

## Objective

Determine whether PI0.5's pinned 10-step Euler denoising cadence causes the
systematic Gate B action bias by comparing it with fixed 20- and 50-step
cadences under the immutable expert-only checkpoint, exact batch, and same five
initial-noise seeds.

## Contract

- Bind T20.35f audit `85c24c5c...`, T20.35d report `13b08e70...`, T20.35c
  result/run/checkpoint, exact target, dataset statistics, processors, model
  revision, parameter boundary, and fixed seeds without mutation.
- Freeze cadence values `[10, 20, 50]`. The 10-step row is the baseline and
  must reproduce all five T20.35d decoded hashes exactly before either candidate
  may be interpreted. Each cadence uses the same initial-noise seed and only
  changes `model.config.num_inference_steps`.
- Preserve the existing objective-ratio pass and 0.05-rad decoded-action gate.
  Gate B passes only if every chunk for one cadence meets the action gate; select
  the smallest passing cadence. If none passes, call cadence directionally
  positive only when one candidate lowers both the worst-seed maximum error and
  aggregate mean error versus baseline; otherwise reject cadence as the cause.
- Create and remotely preserve a signed evaluation spec, one-use permit, tests,
  and pre-run review before model construction. Emit the attempt marker after
  checkpoint-tree verification and before model load.
- Permit one local-MPS model-load/inference evaluation only. Create no optimizer;
  run no training, checkpoint mutation, dataset/statistics change, closed-loop
  rollout, Gate C work, hardware, external compute, or Brev.

## Acceptance Criteria

- Deterministic tests reject source identity, checkpoint, target, baseline hash,
  cadence set/order, seed, metric, paired-selection, gate, route, permit,
  non-finite, and forbidden-action drift.
- The counted result retains every decoded matrix and hash, exact baseline
  reproduction, per-seed metrics, candidate comparisons, and a fail-closed route.
- Pre-run and result reviews, canonical state, ledger, session logs, scoped
  commits, and remote preservation agree before any Gate C work.

## Out Of Scope

Optimizer; training; checkpoint or dataset mutation; normalization or output
correction; additional cadence values; closed-loop execution; Gate C; rollout;
hardware; external compute; Brev; transfer; promotion; or policy acceptance.
