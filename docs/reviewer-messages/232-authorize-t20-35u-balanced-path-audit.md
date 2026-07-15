# Reviewer Decision 232 - Authorize T20.35u Balanced Path Audit

**Decision:** `AUTHORIZE_ONE_T20_35U_INFERENCE_ONLY_TRAJECTORY_AUDIT`

## Reviewed Boundary

Brief 187, implementation `5c99e79`, spec `2575861c...`, permit
`bda88c46...`, T20.35q source paths, T20.35t run/checkpoint/result, runner,
tests, canonical state, and the complete scoped diff were reviewed before
checkpoint tensor access or T20.35u model construction.

## Adversarial Findings

- The exact T20.35t checkpoint tree `aeef380b...` is bound by two file hashes,
  and all T20.35t/Q/result identities must verify before model construction.
- The five base-noise hashes and T20.35p source-path endpoint hashes are copied
  from signed T20.35q evidence; the five expected balanced-checkpoint endpoint
  hashes are copied from signed T20.35t evidence.
- The active-zero/padded-normal mask, five seeds, ten-step time grid, dataset
  target, normalized target, processor stack, and sampler source are unchanged.
- The attempt marker precedes LeRobot activation, checkpoint tensor access,
  model construction, and inference. An existing attempt or result fails
  closed and prevents retry.
- The result recomputes every state/velocity hash and aggregate from captured
  finite trajectories. It can route evidence but hard-codes Gate B false and
  cannot select an action correction.
- Optimizer creation/training, checkpoint/source mutation, rollout, Gate C,
  hardware, external compute, and Brev are all denied.
- Nineteen relevant tests, exact signed spec verification, and an offline
  Python 3.12 preflight pass after remote preservation.

## Disposition

Authorize exactly one Python 3.12 local-MPS T20.35u inference-only audit under
permit `bda88c46...`. Interpret only its signed result. Do not retry, create an
optimizer, train, enter Gate C, access hardware, or start external compute.
