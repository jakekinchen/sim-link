# Reviewer Decision 214 - Verify T20.35j Noise-Scale Positive Non-Pass

**Decision:** `VERIFY_NOISE_SCALE_EFFECT_KEEP_GATE_B_CLOSED`

## Reviewed Boundary

Brief 176, implementation/spec/permit, consumed attempt `61eca0ab...`, signed
result `e9bbff84...`, result commit `06b3a0a`, runtime verifier, relevant tests,
canonical state, and the complete scoped diff were reviewed after the sole
authorized inference attempt.

## Adversarial Findings

- Scale 1.0 reproduces every T20.35g baseline action hash exactly. Each seed's
  base-noise hash is identical across all three scales.
- Scale 0.5 strictly improves worst error, aggregate mean, and raw cross-seed
  spread from `0.150321`/`0.030990`/`0.046392` rad to
  `0.084120`/`0.024630`/`0.018129`.
- Scale 0.0 improves the same metrics to
  `0.073360`/`0.024130`/`0.0`, proving a directional initial-noise effect.
- Neither candidate keeps all decoded values within 0.05 rad. No scale passes
  Gate B, and the zero-noise intervention is not relabeled as a valid policy
  sampler.
- The one-use permit is consumed. There is no retry or hidden additional scale,
  seed, cadence, correction, optimizer, mutation, rollout, or Gate C action.
- The signed verifier, 38 relevant tests, and 6 subtests pass in Python 3.12.
  Every hardware, external-compute, Brev, transfer, promotion, and policy
  acceptance flag remains false.

## Disposition

Accept T20.35j as a verified directionally positive Gate B non-pass. Open only
the model-free T20.35k exact-source sampler/noise-distribution audit under Brief
177. Do not load the model, modify the sampler, create an optimizer, or enter
Gate C.
