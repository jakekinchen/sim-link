# Reviewer Decision 215 - Verify T20.35k Sampler And Noise Audit

**Decision:** `VERIFY_PADDED_NOISE_EXPOSURE_ROUTE_CAUSAL_MASK_TEST`

## Reviewed Boundary

Brief 177, implementation/report commit `357cd6e`, signed audit `bc9f0845...`,
exact active model/config sources, writer/verifier, tests, canonical state, and
the complete scoped diff were reviewed after model-free construction.

## Adversarial Findings

- The parser verifies standard-normal mean 0/std 1 noise is shared by training
  and inference; there is no default prior mismatch.
- Training interpolation is `t*noise + (1-t)*action`, with velocity target
  `noise-action`; inference starts at noise and follows the expected 10-step
  Euler grid.
- Actions are padded from six to 32 for training. Inference also samples 32
  noise dimensions, and all 32 enter the shared action projection.
- Direct training loss and returned actions are both truncated to the first six
  dimensions. The 26 padded dimensions therefore have no direct output loss.
- Source exposure is not causal proof. Half/zero noise are off the default prior
  and are not accepted as a sampler correction.
- Forty-three relevant tests and 14 subtests pass; exact writer verification
  agrees in Python 3.11 and 3.12. All model, checkpoint, optimizer, mutation,
  rollout, Gate C, hardware, external-compute, Brev, and promotion flags remain
  false.

## Disposition

Verify T20.35k. Open T20.35l under Brief 178 to evaluate only the two mixed
active-six/padded-26 masks against T20.35j's signed endpoints. Do not load a
model until a separate pre-run decision and one-use permit are remotely
preserved.
