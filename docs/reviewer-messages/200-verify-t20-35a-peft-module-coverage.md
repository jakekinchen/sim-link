# Reviewer Decision 200 - Verify T20.35a PEFT Module Coverage

**Decision:** `ACCEPT_COVERAGE_FAILURE_ROUTE_EXPERT_ONLY_CAPACITY_CEILING`

## Reviewed Evidence

Brief 167, the signed T20.35 run/result, adapter config, complete checkpoint
tree, every safetensors key/shape/dtype/content identity, deterministic audit,
tests, scoped diff, and remotely preserved implementation `d0be180` were
reviewed together.

## Findings

- All 76 tensors are finite, content-bound, correctly rank 16, and paired; the
  tensor element total exactly matches the run's 1,287,168 trainable count.
- All 36 expected expert-attention q/v modules are present across 18 layers.
- Only two of five required action/state pathways are actually wrapped:
  `action_in_proj` and `action_out_proj`.
- `state_proj`, `action_time_mlp_in`, and `action_time_mlp_out` are absent.
  Their names in the target regex do not prove that PEFT wrapped them.
- The audit loaded no model, ran no inference or optimizer, mutated no
  checkpoint, and touched no hardware or external compute.

## Disposition

Accept T20.35a as verified coverage failure. Defer the 10x learning-rate and
5,000-update rungs. Open T20.35b as exactly one no-LoRA expert-only unfreeze
capacity-ceiling probe on the frozen batch, with a fresh signed specification,
central training-only authority, tests, pre-run review, commit, push, and
remote confirmation before model load or optimizer creation.
