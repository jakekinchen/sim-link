# Slice Brief 165 - T20.34 Gate B Plumbing Localization

**Date:** 2026-07-14

**State:** `verified`

**Implementation boundary:** `491eb6c`

**Result identity:**
`8026980d2f3682dfff515f0e522393cf8c2d2ff090df480d55a203b85ee34c98`

## Objective

Localize the verified-negative T20.33 Gate B result without another optimizer:
determine whether the saved adapter/update path is inert or misbound, or
whether the training objective moves while decoded inference fails to move
consistently toward the exact fixed-batch action target.

## Contract

- Reuse the exact T20.33 source batch, dataset statistics, base snapshot,
  adapter checkpoint, horizon 50, task, coordinate conversion, and five
  inference seeds. No source, threshold, processor, or runtime substitution.
- Verify the complete T20.33 run, result, and checkpoint tree before model
  load. Record LoRA tensor coverage, finite norms, and nonzero values directly
  from the saved adapter.
- With no optimizer and no gradient, decode one base chunk and one adapter
  chunk for each declared seed under identical observations and seeds. The
  adapter rerun must reproduce every T20.33 decoded-action hash exactly.
- Compare base and adapter objective means, complete-chunk MAE/max error,
  per-joint error, adapter-minus-base movement, target-minus-base direction,
  and cosine alignment for each seed.
- Route exactly one result: `adapter_checkpoint_plumbing` if saved weights are
  zero/missing or outputs are unchanged; `objective_to_inference_alignment` if
  the adapter is active but mean decoded error does not improve consistently;
  or `insufficient_gate_b_optimization_or_capacity` if active decoded outputs
  move consistently toward the target yet remain outside Gate B.
- No optimizer, dataset/statistics/twin change, closed-loop rollout, hardware,
  camera, Robo Scan artifact, external compute, Brev, policy acceptance,
  transfer, or promotion.

## Acceptance Criteria

- Tests reject checkpoint, tensor, source, seed, hash-replay, non-finite,
  unchanged-output, routing, and authority mutation.
- One signed report binds base/adapter hashes, objectives, per-seed/per-joint
  decoded errors and movement, and exactly one routed Gate B hypothesis.
- Focused and broad tests, same-agent adversarial review, state, ledger, plan,
  session log, reviewer decision, scoped commits, and remote preservation
  agree before T20.34 is verified.

## Out Of Scope

Any optimizer or retry; a second batch; Gate C cadence/chunk/feedback changes;
full-dataset or held-out evaluation; closed-loop rollout; promotion; hardware;
external compute; Brev; or global authority change.

## Verified Result

The T20.33 adapter is active and correctly reloaded: 321,688 of 321,792 saved
values are nonzero, and all five decoded action hashes reproduce exactly.
Compared with the pinned base under identical seeds, adapter mean action error
improves by 0.0553-0.0826 rad on every seed and movement-to-target cosine is
positive on every seed (0.456-0.856). The objective also reproduces exactly
at 0.959079 base and 0.506632 adapter. Dead/misbound checkpoint plumbing and
objective-to-inference opposition are rejected. The routed hypothesis is
`insufficient_gate_b_optimization_or_capacity`; Gate B remains unmet.
