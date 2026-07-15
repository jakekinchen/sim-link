# Reviewer Decision 216 - Authorize T20.35l Noise-Mask Evaluation

**Decision:** `AUTHORIZE_ONE_T20_35L_INFERENCE_ONLY_MIXED_MASK_EVALUATION`

## Reviewed Boundary

Brief 178, implementation `2f04395`, spec `4c346688...`, permit `5b990e78...`,
T20.35j/k sources, runner, tests, canonical state, and the complete scoped diff
were reviewed before model or checkpoint tensor access.

## Adversarial Findings

- All-normal and all-zero endpoints are inherited from signed T20.35j chunks;
  they are not rerun or reinterpreted.
- Exactly two new conditions exist: active-six normal/padded-26 zero and its
  active-zero/padded-normal complement. The masks sum to one in every dimension.
- Checkpoint, batch, target, processors, five seeds, 10 denoising steps, source
  hashes, and 0.05-rad gate are unchanged.
- Before each new inference, the runner resamples the standard-normal tensor and
  requires its exact T20.35j per-seed base-noise hash.
- Positive classification requires worst error, aggregate mean, and cross-seed
  spread all strictly improve over all-normal. Gate B still requires every
  decoded action within 0.05 rad.
- The attempt marker is written after authority/source/checkpoint-tree checks
  and before model import or checkpoint tensor access. Existing attempt/result
  files fail closed; the permit is one-use.
- Sixty relevant tests and 17 subtests pass. Spec and permit verify under both
  configured Python runtimes. The runner exposes no optimizer, training,
  mutation, rollout, Gate C, hardware, external-compute, or Brev path.

## Disposition

After this review and remote preservation, authorize exactly one Python 3.12
local-MPS model-load/inference evaluation under permit `5b990e78...`. Interpret
only its signed result. Do not retry, add a mask/seed, create an optimizer,
enter Gate C, or mutate any source.
