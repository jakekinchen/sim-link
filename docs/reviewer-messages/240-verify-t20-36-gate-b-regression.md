# Reviewer Decision 240 - Verify T20.36 Gate B Regression

**Decision:** `VERIFY_T20_36_NEGATIVE_STOP_BEFORE_GATE_C_ROUTE_OBJECTIVE_INTERFERENCE_AUDIT`

## Reviewed Boundary

Brief 191; implementation commits `8da3cae` and `18f81e7`; pre-run Decision
239; consumed attempt `6513bfd2...`; signed run `88daae0d...`; checkpoint
`c5e36cca...`; signed result `02b543be...`; exact verifier; result commit
`3e1f2bd`; and the complete scoped evidence.

## Adversarial Findings

- Exactly one attempt consumed the one-use permit. All 500 optimizer updates
  completed, with 500 unique coverage samples and no retry.
- The final standard objective is `0.02931348`, or `0.03056419` of the frozen
  original Gate B baseline. This passes the unchanged 0.10 ratio threshold.
- Every decoded chunk fails the unchanged 0.05-rad constraint. Maximum errors
  are `0.166008`, `0.150601`, `0.187035`, `0.160021`, and `0.153113` rad.
- The joint-weighted correction objective improves from `0.00260035` to
  `0.00133429`, while the raw correction objective worsens from `0.0252181` to
  `0.0389846`. A low weighted mean therefore did not preserve the physical
  maximum-error conjunction under coverage training.
- The runner correctly records `gate_b_passed=false` and
  `gate_b_regressed_stop_before_closed_loop`. It reaches no seed, trace, or
  mirror and does not relabel the completed optimizer run as policy success.
- Dataset and statistics were unchanged. The source checkpoint was not
  mutated. Physical actuation, external compute, and Brev were false.
- The signed result verifies byte-for-byte after remote preservation. The
  duplicate AVFoundation class warnings remain nonfatal; no camera was opened.

## Disposition

Verify T20.36 as a bounded negative result. The one-use permit is consumed and
no second campaign, Gate B threshold change, Gate C rollout, or held-out
evaluation is authorized. Open Brief 192 for T20.36a to audit only the already
signed objective histories and Gate B outcomes. Any later model, inference,
optimizer, gate amendment, or policy-track decision requires a separate
reviewed boundary.
