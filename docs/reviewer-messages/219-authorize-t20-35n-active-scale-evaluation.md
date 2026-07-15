# Reviewer Decision 219 - Authorize T20.35n Active-Scale Evaluation

**Decision:** `AUTHORIZE_ONE_T20_35N_INFERENCE_ONLY_ACTIVE_SCALE_EVALUATION`

## Reviewed Boundary

Brief 180, implementation `04f7d3b`, spec `155d9336...`, permit `f821bd57...`,
T20.35l/m sources, runner, tests, canonical state, and the complete scoped diff
were reviewed before model or checkpoint tensor access.

## Adversarial Findings

- Active-scale 0 and 1 endpoints are inherited from signed T20.35l chunks and
  are not rerun. Exactly two new scales exist: 0.25 and 0.5.
- Only dimensions 0-5 are scaled. Dimensions 6-31 remain standard-normal scale
  1.0 for every endpoint and candidate.
- Checkpoint, batch, target, processors, five seeds, 10 steps, source hashes,
  and the 0.05-rad gate are unchanged.
- Before each inference, the runner regenerates the base tensor and requires its
  exact T20.35l per-seed hash.
- Gate B requires every decoded action within 0.05 rad and prefers the largest
  passing scale. Non-passing selection is lowest worst error, then mean, then
  largest scale.
- The attempt marker precedes model import/checkpoint tensor access. Existing
  attempt or result files fail closed; the permit is one-use.
- Fifty-seven relevant tests and 24 subtests pass. Spec and permit verify under
  Python 3.11 and 3.12. No optimizer, training, mutation, rollout, Gate C,
  hardware, external-compute, or Brev path exists.

## Disposition

After remote preservation, authorize exactly one Python 3.12 local-MPS
model-load/inference attempt under permit `f821bd57...`. Interpret only its
signed result. Do not retry, add scales/seeds, create an optimizer, enter Gate C,
or mutate any source.
