# Reviewer Decision 221 - Authorize T20.35o Flow-Trajectory Audit

**Decision:** `AUTHORIZE_ONE_T20_35O_INFERENCE_ONLY_FLOW_TRAJECTORY_AUDIT`

## Reviewed Boundary

Brief 181, implementation `100a76e`, spec `c21c4d48...`, permit
`65c516f3...`, T20.35n source result `d3e6e5d9...`, runner, tests, canonical
state, and the complete scoped diff were reviewed before model or checkpoint
tensor access.

## Adversarial Findings

- The sole condition is the signed active-zero/padded-normal endpoint. Active
  dimensions 0-5 start at zero and padded dimensions 6-31 retain the exact
  per-seed standard-normal tensor.
- Checkpoint, batch, target, processors, five seeds, 10 steps, sampler source,
  and all five decoded endpoint hashes are inherited exactly from T20.35n.
- The runner captures each pre-update state and learned velocity without
  changing the Euler update. It rejects live time-grid drift and restores the
  original denoise method after every call.
- The normalized 50x32 target is bound in the signed result; padded target
  dimensions must be exactly zero. Every reference residual is recomputed as
  `learned_velocity - (state-target)/time` from retained finite tensors.
- Classification is fail-closed and diagnostic: late-step concentration is
  checked first, then dominant active-channel concentration, otherwise the
  residual is distributed. No class can pass Gate B or select an action
  correction.
- The attempt marker precedes model import and checkpoint tensor access.
  Existing attempt or result files fail closed; the permit is one-use.
- Eleven relevant tests pass under Python 3.12, the six new tests pass under
  Python 3.11, and exact spec/permit verification agrees in both runtimes. No
  optimizer, training, mutation, rollout, Gate C, hardware, external compute,
  or Brev path exists.

## Disposition

After remote preservation, authorize exactly one Python 3.12 local-MPS
model-load/inference attempt under permit `65c516f3...`. Interpret only its
signed result. Do not retry, add a condition/seed/step, create an optimizer,
enter Gate C, or mutate any source.
