# Slice Brief 167 - T20.35a PEFT Module Coverage Audit

**Date:** 2026-07-15

**State:** `verified`

## Objective

Determine whether T20.35's actual saved LoRA tensors cover every declared
PI0.5 action/state adaptation pathway before spending another Gate B optimizer
rung.

## Contract

- Bind the signed T20.35 run, result, adapter config, and safetensors file by
  exact content identity.
- Enumerate every saved LoRA tensor key, shape, dtype, element count, and
  nonzero count without constructing PI0.5, running inference, or creating an
  optimizer.
- Require paired `lora_A` and `lora_B` tensors for every wrapped module and
  reject duplicate, unpaired, malformed, non-finite, unexpected, or
  content-drifting evidence.
- Classify actual module coverage separately for expert attention projections
  and the five required action/state pathways: `state_proj`, `action_in_proj`,
  `action_out_proj`, `action_time_mlp_in`, and `action_time_mlp_out`.
- Coverage passes only if all five required action/state pathways are actually
  present as saved trainable LoRA pairs. A target-module regex that names a
  pathway is not evidence that PEFT wrapped it.
- If coverage is incomplete, route to the plan's separately reviewed
  expert-only unfreeze capacity-ceiling probe before any learning-rate or
  update-budget rung. If complete, route next to the optimizer-free attainable
  loss-floor audit.

## Acceptance Criteria

- Deterministic tests cover complete, missing, unpaired, malformed,
  non-finite, unexpected, and signed-mutation cases.
- One signed audit reproduces exactly from the immutable T20.35 adapter and
  makes one coverage pass/fail decision.
- Focused and relevant broad tests, same-agent adversarial review, state,
  ledger, plan, session log, reviewer decision, scoped commits, and remote
  preservation agree.

## Out Of Scope

Model construction; inference; optimizer training; changing PEFT targets;
learning-rate or update-budget probes; checkpoint mutation; Gate C work;
closed-loop rollout; policy acceptance; hardware; cameras; serial devices;
external compute; Brev; transfer; or promotion.

## Result

Audit `d1109ae8...` verifies 76 finite saved tensors, 1,287,168 elements,
38 paired modules, and complete q/v coverage across all 18 expert-attention
layers. Only `action_in_proj` and `action_out_proj` are wrapped among the five
required action/state pathways. `state_proj`, `action_time_mlp_in`, and
`action_time_mlp_out` are absent. Coverage fails and routes to a separately
reviewed no-LoRA expert-only unfreeze capacity-ceiling probe. No model,
inference, optimizer, or authority change occurred.
