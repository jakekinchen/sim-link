# Reviewer Decision 211 - Verify T20.35h Bias Ceiling

**Decision:** `VERIFY_MIXED_NEGATIVE_AND_ROUTE_RESIDUAL_VARIANCE_LOCALIZATION`

## Reviewed Boundary

Brief 174, T20.35g source result, implementation and artifact commit
`68b7115`, artifact `63e1181b...`, writer/verifier, tests, canonical state,
and the complete scoped diff were reviewed after model-free construction.

## Adversarial Findings

- Every fold holds out exactly one of the five fixed seeds; correction values
  use only the other four. Seed order, correction hashes, corrected-chunk
  hashes, and source identity are bound.
- Global-channel correction strictly improves worst and aggregate error to
  `0.113302` and `0.019781` rad, but all five folds fail and 159 elements remain
  above `0.05` rad.
- Time-conditioned correction strictly improves aggregate mean to `0.017710`
  rad and reduces exceedances to 96, but its worst fold remains `0.136460` rad.
  It does not pass the analytical ceiling.
- The artifact correctly leaves `gate_b_passed`, `action_correction_selected`,
  and `simulation_policy_accepted` false. A post-hoc target-derived correction
  is not a model capability claim.
- Cross-runtime replay permits only `1e-15` derived-float drift. Signed payload
  integrity, source IDs, hashes, types, counts, routes, and non-float truth
  fields remain exact.
- Six focused and 76 relevant tests pass. No model, checkpoint, inference,
  optimizer, mutation, rollout, hardware, external compute, or Brev action
  exists in the implementation.

## Disposition

Accept T20.35h as a verified mixed-negative discriminator. Route T20.35i to
model-free localization of the remaining time-conditioned errors by seed,
channel, timestep, and pairwise decoded spread. Do not select a correction,
load a model, create an optimizer, or enter Gate C.
