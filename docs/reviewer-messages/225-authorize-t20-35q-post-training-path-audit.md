# Reviewer Decision 225 - Authorize T20.35q Post-Training Path Audit

**Decision:** `AUTHORIZE_ONE_T20_35Q_INFERENCE_ONLY_PATH_COMPARISON`

## Reviewed Boundary

Brief 183, implementation `fbc1087`, spec `fdb2fe3e...`, permit
`ab85aede...`, T20.35o source trajectories, T20.35p checkpoint/result, runner,
tests, canonical state, and the complete scoped diff were reviewed before
checkpoint tensor access.

## Adversarial Findings

- The new checkpoint tree `9358cee4...`, exact processors/target, five base
  tensors, active-zero/padded-normal mask, 10-step grid, and five T20.35p
  endpoint hashes are frozen.
- Exactly five inference calls are allowed. The runner captures each new
  pre-update state and learned velocity without changing the Euler update and
  restores the original denoise method after each call.
- The signed result retains every new tensor. Its verifier recomputes new and
  source target residuals plus active/padded state and velocity displacement
  from T20.35o's immutable source path.
- Material residual worsening and path displacement thresholds are both 0.01
  normalized units. Dominant padded-state movement routes padded coupling;
  otherwise any material divergence by step 6 routes early/mid-path
  interference, and later divergence routes off-trajectory supervision.
- Gate B is forced false and no classification selects an action correction or
  opens Gate C.
- The immutable attempt marker precedes model import and checkpoint tensor
  access. Existing attempt/result files fail closed; the permit is one-use.
- Forty relevant tests pass under Python 3.12, the four new tests pass under
  Python 3.11, and spec/permit/model-free runner preflight verify exactly. No
  optimizer, training, rollout, hardware, external compute, or Brev path
  exists.

## Disposition

After remote preservation, authorize exactly one Python 3.12 local-MPS
inference-only attempt under permit `ab85aede...`. Interpret only its signed
result. Do not retry, train, add a condition/seed/step, enter Gate C, or mutate
any source.
