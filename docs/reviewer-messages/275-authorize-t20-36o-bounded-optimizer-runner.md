# Reviewer Decision 275 - Authorize T20.36o Optimizer Runner Implementation

**Decision:** `VERIFY_OPTIMIZER_AUTHORITY_AUTHORIZE_RUNNER_IMPLEMENTATION`

## Reviewed Boundary

Brief 208; spec `50e0569d...`; implementation `ae9992b` on origin; owner grant
`dee9ae59...`; request `c325cb12...`; decision `8834322d...`; preflight
`672c59cc...`; permit `f9bad1ae...`; exact materializer verification; 31
combined tests; file identities; and the complete scoped diff.

## Findings

- Central decision `8834322d...` grants only `simulation_training_ready` and
  withholds physical transfer and promotion.
- Runtime preflight `672c59cc...` binds source/origin `ae9992b`, exact X
  checkpoint and frozen-base trees, Python 3.12/MPS dependency versions,
  85.20 GB free, and absent attempt/result/output-checkpoint paths.
- One-use permit `f9bad1ae...` binds all 2,500 correction indices, 2,500 unique
  replay seeds, five 500-update probe points, five starts, five seeds, two
  repeats, first confirmed pass, and no retry.
- Update 0 is the retained exact baseline `e6537428...`; it may not be decoded
  again. A live run may perform at most 2,500 updates and stop earlier only on
  an immediate confirmed complete pass.
- The attempt marker must precede checkpoint tensor deserialization, model
  construction, and optimizer creation.
- Gate C, threshold change, second attempt, hardware, network, external
  compute, and Brev remain closed.
- No marker, model, optimizer, training action, output checkpoint, or result
  exists at review time.

## Disposition

Verify and remotely preserve this authority boundary. Next implement and test
the permit-bound runner and probe/result/checkpoint contracts. Do not create a
model or optimizer until that runner receives a separate pre-run review and is
also preserved on origin.

## Withheld Authority

No model construction/load or optimizer action before runner review and remote
preservation; no retry, Gate C, threshold change, hardware, network, external
compute, or Brev.
