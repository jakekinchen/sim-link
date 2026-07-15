# Reviewer Decision 213 - Authorize T20.35j Noise-Scale Evaluation

**Decision:** `AUTHORIZE_ONE_T20_35J_INFERENCE_ONLY_NOISE_SCALE_EVALUATION`

## Reviewed Boundary

Brief 176, implementation `ed05689`, spec `a3dc0acb...`, permit
`545a71c6...`, T20.35i route, exact T20.35g sources, sampler source, runner,
tests, canonical state, and the complete scoped diff were reviewed before
model or checkpoint tensor access.

## Adversarial Findings

- The only candidate factor is initial-noise multiplication after the pinned
  standard-normal sampler: scales are exactly `1.0`, `0.5`, and `0.0`.
- Checkpoint, target, processors, five seeds, 10 denoising steps, and action
  gate are unchanged. Scale 1.0 must reproduce all five signed action hashes.
- Each scale/seed pair resets the same torch seed, samples through the pinned
  source, records the base-noise hash, and fails if any scale receives a
  different base tensor for that seed.
- Gate B requires all five chunks within 0.05 rad. A non-passing positive
  result must strictly improve worst error, aggregate mean, and aggregate raw
  spread together. The largest passing scale has priority.
- The attempt marker is written after source/authority/checkpoint-tree checks
  and before model/checkpoint tensor access. Existing attempt or result files
  fail closed; the permit is one-use.
- Five focused and 86 relevant tests pass. Spec and permit verify in both
  configured Python runtimes.
- The runner constructs no optimizer and exposes no training, mutation,
  rollout, Gate C, hardware, external-compute, or Brev path.

## Disposition

After this review and remote preservation, authorize exactly one Python 3.12
local-MPS model-load/inference evaluation under permit `545a71c6...`. Interpret
only its signed result. Do not retry, add scales/seeds, create an optimizer,
enter Gate C, or mutate any source.
