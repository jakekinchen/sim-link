# Slice Brief 124 - T20.4 PI0.5 Optimizer-Update Ladder

**Date:** 2026-07-14

## Objective

Run the first explicit PI0.5 optimizer-update ladder rung over the source-bound
T20.1 training split and determine whether substantially more bounded
optimization changes held-out strict grasp behavior. Start with 250 optimizer
updates; do not run 500 or 1,000 updates unless the smaller rung's reviewed
evidence justifies the added compute.

## Contract

- Revalidate live T20.1 central simulation authority immediately before model
  load and optimization. Use local MPS only. Network, hardware, external
  compute, and Brev are forbidden.
- Preserve T20.3's exact T20.1 spec/tensor hashes, cached checkpoint,
  tokenizer, processor, normalization, prompt, canonical coordinates, rank-4
  LoRA scope, learning rate, train seeds, and held-out seed.
- Define one optimizer update as exactly two finite microbatch losses, each
  divided by the accumulation count before backward. Clip gradients once and
  step the optimizer once after both microbatches. Record optimizer updates,
  microbatch count, accumulation factor, every source start, per-update mean
  loss, and pre-clip gradient norm without conflating these quantities.
- Fail closed on any episode-boundary crossing, non-finite loss or gradient,
  source/checkpoint drift, expired authority, or existing output path. Save an
  immutable adapter and summary with exact hashes.
- Evaluate the 250-update adapter separately on all 244 held-out seed-2 MuJoCo
  frames with policy-owned controls, exact pre/postprocessing, five-action
  replans, zero semantic assist, measured projections, strict-v2 gate margins,
  and three to five 256 px keyframes.
- Loss reduction is diagnostic only. Promotion remains false unless strict
  semantic success is independently demonstrated and reviewed.

## Acceptance Criteria

- The 250-update rung records exactly 500 microbatches and 250 optimizer steps,
  with finite losses/gradients and source starts that all remain within episode
  boundaries.
- A fresh signed held-out rollout records terminal outcome, policy behavior,
  strict semantic success, and gate margins separately.
- Review explicitly decides whether the evidence justifies a 500-update rung,
  a corrective hypothesis, or stopping the ladder.

## Out Of Scope

Unreviewed 500/1,000-update execution, model bake-offs, physical hardware,
external compute, Brev, checkpoint promotion, and destructive cleanup.
