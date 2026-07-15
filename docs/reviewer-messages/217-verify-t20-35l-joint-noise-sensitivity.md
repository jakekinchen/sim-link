# Reviewer Decision 217 - Verify T20.35l Joint Noise Sensitivity

**Decision:** `VERIFY_JOINT_SENSITIVITY_KEEP_GATE_B_CLOSED`

## Reviewed Boundary

Brief 178, implementation/spec/permit, consumed attempt `adf33ca1...`, signed
result `b4fc6060...`, result commit `1040478`, runtime verifier, tests,
canonical state, and the complete scoped diff were reviewed after the sole
authorized inference attempt.

## Adversarial Findings

- Both inherited endpoints remain exact; each new call uses the signed per-seed
  base-noise hash and the two masks are exact complements.
- Removing padded noise alone improves worst/mean/spread from
  `0.150321`/`0.030990`/`0.046392` to
  `0.114173`/`0.028504`/`0.034544` rad.
- Removing active-six noise alone improves them further to
  `0.066398`/`0.020908`/`0.009970`, the best tested condition.
- All-zero reaches `0.073360`/`0.024130`/`0.0`; padded noise therefore has a
  context-dependent effect on worst and mean error rather than a simple always-
  harmful nuisance interpretation.
- No condition stays within 0.05 rad. Gate B and Gate C remain closed.
- The one-use permit is consumed. No retry, optimizer, training, mutation,
  correction, rollout, hardware, external compute, or Brev action occurred.

## Disposition

Accept joint active/padded noise sensitivity without claiming a fix. Open only
the model-free T20.35m signed factorial interaction audit under Brief 179.
