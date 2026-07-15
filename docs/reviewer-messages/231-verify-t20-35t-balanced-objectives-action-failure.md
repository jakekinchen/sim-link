# Reviewer Decision 231 - Verify T20.35t Balanced Objectives And Action Failure

**Decision:** `VERIFY_BALANCED_OBJECTIVES_PASS_ACTION_FAIL_ROUTE_PATH_AUDIT`

## Reviewed Boundary

Brief 186, implementation/spec/authority, consumed attempt `1a94b476...`, run
`b5da8ab3...`, checkpoint `aeef380b...`, signed result `f63ee934...`, result
commit `41238de`, verifiers, canonical state, and the complete scoped diff were
reviewed after the sole authorized attempt.

## Adversarial Findings

- All 500 paired updates completed with finite objectives and gradients; each
  of 50 exact path examples was used 10 times and each update replayed one
  unique frozen standard-objective seed. The T20.35p source checkpoint tree is
  unchanged.
- The raw full-path correction ratio is `0.051751`, below 0.10. The standard
  objective falls from `0.044581` to `0.005989`, producing an unchanged
  original-baseline ratio of `0.006245`, also below 0.10.
- Every decoded action chunk still fails 0.05 rad. Mean errors are
  `0.021005-0.043490` rad, but maximum errors are `0.084388-0.162008` rad.
- All five mean action errors improve over T20.35p, and four of five maximum
  errors improve. That progress does not relax the all-chunks action gate.
- Passing both scalar objectives while failing actions isolates a remaining
  inference-path problem, but endpoint metrics alone cannot distinguish
  transient target-residual worsening, source-path displacement, or a
  late-coordinate outlier.
- Gate B and Gate C remain closed. No retry, rollout, hardware, external
  compute, or Brev action occurred.

## Disposition

Verify T20.35t as a controlled action-only negative. Open T20.35u under Brief
187 for one inference-only post-training trajectory audit of the balanced
checkpoint. Do not create an optimizer, train again, or enter Gate C.
