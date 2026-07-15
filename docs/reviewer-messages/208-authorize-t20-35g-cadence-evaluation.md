# Reviewer Decision 208 - Authorize T20.35g Cadence Evaluation

**Decision:** `AUTHORIZE_ONE_T20_35G_INFERENCE_ONLY_CADENCE_EVALUATION`

## Reviewed Boundary

Brief 173, implementation `88602b0`, spec `be1c50f3...`, permit `ca3dbd3f...`,
T20.35f route, immutable checkpoint/batch/baseline sources, runner, tests,
canonical state, and complete scoped diff were reviewed before model load.

## Adversarial Findings

- The spec binds T20.35f audit `85c24c5c...`, T20.35d report `13b08e70...`,
  expert-only run/checkpoint `9b1af8ee...` / `439ae119...`, exact target, fixed
  seeds, parameter boundary, and source objective-ratio pass.
- Cadence values and order are exactly 10, 20, and 50. The runner resets the
  action queue and initial torch seed for every cadence/seed pair, changing only
  `model.config.num_inference_steps`.
- The 10-step baseline must reproduce all five signed T20.35d hashes before the
  20- or 50-step rows can be interpreted. No tolerance substitutes for hashes.
- Gate B action success requires every fixed seed at or below 0.05 rad. The
  smallest passing candidate wins. Without a pass, positive cadence evidence
  requires strict improvement in both worst-seed maximum and aggregate mean.
- The attempt marker is written after checkpoint-tree verification and before
  model load. Existing attempt or result files fail closed; the permit is one-use.
- The runner constructs no optimizer and exposes no training, checkpoint/data
  mutation, rollout, Gate C, hardware, external-compute, or Brev path.
- Four focused and 88 relevant tests pass, including source/checkpoint, cadence,
  seed, baseline hash, metric, selection, route, permit, non-finite, and
  forbidden-action adversaries. Spec and permit reproduce exactly.

## Disposition

After this review and remote preservation, authorize exactly one local-MPS
T20.35g model-load/inference evaluation under permit `ca3dbd3f...`. Interpret
only its signed result. Do not create an optimizer, add cadence values, enter
Gate C, or mutate any source.
