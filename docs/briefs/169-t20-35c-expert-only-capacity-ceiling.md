# Slice Brief 169 - T20.35c Expert-Only Capacity Ceiling

**Date:** 2026-07-15

**State:** `in_progress`

## Objective

Test whether complete PI0.5 action-expert adaptation can satisfy the exact
T20.33 one-batch Gate B proof when LoRA coverage is removed as the limiting
factor.

## Contract

- Reuse byte-for-byte the T20.33 source batch, dataset statistics, base model,
  task, processor/postprocessor path, horizon, constant `2.5e-5` learning
  rate, 500 updates, training seed, five inference seeds, objective-ratio
  gate, and `0.05` rad all-chunk action gate.
- Use no PEFT wrapper, LoRA adapter, rank, or alpha. Set
  `train_expert_only=true` and mechanically require the entire PaliGemma
  parameter tree to be frozen.
- Train exactly the Gemma action expert plus `action_in_proj`,
  `action_out_proj`, `time_mlp_in`, and `time_mlp_out`. Reject any trainable
  PaliGemma parameter, missing required prefix, stale `action_time_mlp_*`
  prefix, or nonexistent `state_proj` expectation.
- Bind corrected coverage audit `446a0686...`, the pinned LeRobot stack and
  source identities, and the exact trainable-name/shape/dtype boundary exposed
  after model construction.
- Produce a new signed specification, owner-scope grant, central-composer
  request, and `simulation_training_ready` decision. Tests, same-agent pre-run
  review, state, commit, push, and remote confirmation must agree before model
  construction or optimizer creation.
- Run exactly once from the clean pinned base. Write a signed immutable attempt
  marker before model construction; record every finite objective and gradient,
  the trainable-only checkpoint, and five full decoded chunks. No retry,
  continuation, second adaptation mode, second batch, or hyperparameter change.
- Gate B passes only under the unchanged T20.33 criteria: every decoded chunk
  maximum error `<= 0.05` rad and final five-seed objective `<= 10%` of
  baseline. A failure remains a verified negative and blocks Gate C and broader
  campaigns.
- No closed-loop rollout, dataset/statistics/twin change, hardware, camera,
  external compute, Brev, policy acceptance, transfer, or promotion.

## Acceptance Criteria

- Deterministic tests reject PEFT/LoRA use, adaptation-boundary drift, source,
  update, seed, threshold, non-finite, checkpoint, retry, result, and authority
  mutation.
- Pre-run implementation and central training-only authority are reviewed and
  remotely preserved before the sole model/optimizer attempt.
- One signed result makes exactly one pass/fail decision and compares the
  expert-only capacity ceiling with the frozen rank-16 boundary without
  relabelling either.
- Focused and relevant broad tests, adversarial review, canonical state,
  ledger, session log, reviewer decisions, scoped commits, and remote
  preservation agree.

## Out Of Scope

Any PEFT or LoRA configuration; changing learning rate, update budget, batch,
seed, processor, target, or gate; retry; continuation; Gate C work; campaign;
closed-loop rollout; promotion; hardware; external compute; Brev; or global
authority change.
