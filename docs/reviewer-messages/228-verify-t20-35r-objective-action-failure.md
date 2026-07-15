# Reviewer Decision 228 - Verify T20.35r Objective And Action Failure

**Decision:** `VERIFY_FULL_PATH_CORRECTION_NEGATIVE_ROUTE_OBJECTIVE_MASS_AUDIT`

## Reviewed Boundary

Brief 184, implementation/spec/authority, consumed attempt `fbcc16a5...`, run
`85826156...`, checkpoint `b73123dc...`, signed result `52d4c9ed...`, result
commit `c8f75a0`, verifiers, tests, canonical state, and the complete scoped
diff were reviewed after the sole authorized attempt.

## Adversarial Findings

- All 500 updates completed with finite objectives and gradients; each of 50
  exact path examples was used exactly 10 times. The T20.35p source checkpoint
  tree is unchanged.
- Correction objective falls from `0.120801` to `0.011514`, ratio `0.095317`,
  and 41 of 50 individual examples improve.
- Count balance did not imply objective-mass balance. Steps 8–9 contain
  `90.2746%` of baseline correction objective mass and step 9 alone contains
  `77.5851%`. Steps 3 and 4 regress after correction.
- The standard objective rises from `0.044581` to `0.144311`, a `3.23704x`
  increase and `0.150468` of the original Gate B baseline, so the unchanged
  objective gate fails.
- Every decoded chunk also fails 0.05 rad; maxima are
  `0.114470–0.197005`. Gate B and Gate C remain closed.
- This result proves a correction/standard compatibility failure but does not
  yet prove that late-time objective mass caused it. That attribution must be
  made by a deterministic audit, not by another optimizer run.
- No retry, rollout, hardware, external compute, or Brev action occurred.

## Disposition

Verify T20.35r as a clean negative. Open T20.35s under Brief 185 for one
model-free time-step objective-mass and standard-compatibility audit. Do not
load a model, train again, or enter Gate C.
