# Reviewer Decision 236 - Verify T20.35w Physical-Gate Joint Dominance

**Decision:** `VERIFY_PHYSICAL_GATE_JOINT_DOMINANCE_ROUTE_WEIGHTED_CORRECTION`

## Reviewed Boundary

Brief 189, implementation/audit `e52d6d08...`, commit `99cbbc4`, exact
verifier, 27 relevant tests, canonical state, and the complete scoped diff
were reviewed without model or checkpoint access.

## Adversarial Findings

- All five decoded endpoint hashes and the immutable 50-by-6 target verify.
  The audit recomputes exactly 1,500 finite seed/action/joint errors.
- 370 cells (`24.6667%`) exceed 0.05 rad. The top 5% of cells hold only
  `36.4067%` of squared error, so the failure is not sparse.
- Shoulder lift alone carries `50.6574%` of physical-radian squared error and
  has 196 exceedances; wrist roll carries `29.3595%` with 116 exceedances.
  Together they account for `80.0168%`.
- The first ten actions carry `42.1972%` of squared error, below the explicit
  50% time-band threshold. No time band dominates.
- Last-captured normalized-state error is distributed: elbow flex is largest
  at only `20.7126%`, and shoulder lift is `17.6644%`. Physical-radian joint
  dominance therefore is not mirrored by normalized-state dominance.
- This supports a physical-gate/normalization weighting mismatch. It does not
  justify changing the uniform 0.05-rad gate or relabeling the action result.
- A next correction must preserve deterministic standard replay because that
  mechanism produced T20.35t's standard-objective pass.
- Gate B and Gate C remain closed. Model load, checkpoint access, inference,
  optimizer, rollout, hardware, external compute, and Brev are false.

## Disposition

Verify T20.35w. Open T20.35x under Brief 190 to design and separately authorize
one current-path, physical-gate-aligned joint-weighted full-path correction
with deterministic standard replay. Do not load a model or create an optimizer
before that boundary is remotely preserved.
