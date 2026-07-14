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

## Interim Reviewed 250-Update Rung

The exact 250-update/500-microbatch run completed with all losses and gradients
finite and 390 unique valid train starts. Train loss changed from
100.84408569335938 to 32.25172805786133; held-out loss changed from
130.006591796875 to 31.422643661499023. The saved adapter changed the policy
action sequence, but the 244-frame strict held-out rollout still made zero
strict-v2 contacts and lifted only 0.00000030070669393422733 m against the
0.025 m threshold. It used zero assist and zero action projections and retained
five 256 px keyframes with measured gate margins.

Reviewer 152 authorizes one independent 500-total-update rung because the loss
signal is large, finite, and directionally consistent. This is a bounded
falsification test, not a promotion. The 1,000-update rung remains outside
authority until the 500-update behavior is reviewed.

## Verified 500-Update Outcome

The exact 500-update/1,000-microbatch run remained finite and reduced train
loss to 6.476014852523804 and held-out loss to 1.8620187640190125. Its strict
held-out action sequence changed again but still produced zero strict-v2
contacts, zero assist or projection frames, and only
0.00000030070669393422733 m lift. The initial action retained 0.1507563 rad
mean absolute error against the held-out expert command, including 0.6551162
rad on the gripper coordinate. Reviewer 153 retires the 1,000-update rung for
this hypothesis and closes T20.4 as verified negative evidence.
