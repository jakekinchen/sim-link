# Reviewer Decision 261 - Verify T20.36k Consequence Calibration

**Decision:** `VERIFY_NON_AUTHORIZING_CALIBRATION_OPEN_FROZEN_AMENDMENT`

## Reviewed Boundary

Brief 204; implementation `fbdb0aad4f268268ae567836fc69866c97e528b1`;
result `a3b391784eaca8fef2cb9ff6abe45cc21346cada8f9483be60692dac0faf1f66`;
exact verifier; canonical seed-0 replay; 252 symmetric perturbation pairs; 42
derived phase/joint rows; source bindings; 13 focused tests; 82 broader
T20.36 tests with 80 passes and two expected post-install historical-state
mismatches; origin parity; and the complete scoped diff.

## Findings

- The exact 244-action source replay passes every strict-v2, contact, safety,
  release, retreat, projection, and assistance predicate.
- The perturbation grid is fixed independently of candidate errors: six
  joints, seven exhaustive phase groups, magnitudes 0.01/0.025/0.05/0.1/0.2/
  0.4 rad, and both signs.
- Of 252 symmetric pairs, 202 pass and 50 fail. All 42 phase/joint response
  rows are monotonic, so no later pass reopens a failed threshold prefix.
- Wrist roll remains consequence-insensitive through 0.4 rad in every phase.
  Shoulder lift is task-critical at 0.025 rad during lift; gripper is
  task-critical at 0.01 rad during lift, hold, and lower.
- Candidate results are contextual references only. The verifier rejects
  candidate-derived thresholds, grid drift, pair drift, delta drift, source
  drift, non-finite values, and authority escalation.
- Historical 0.05-rad uniform error and 0.10 objective ratio remain visible.
  Gate B is not amended here; Gate C, policy acceptance, hardware, external
  compute, and Brev remain false.

## Disposition

Verify T20.36k as a non-authorizing consequence calibration. Open Brief 205
only: freeze the evidence-derived amendment and score immutable retained ACT
and SmolVLA tensors without model loading or inference. Any pass routes to a
separate one-training-episode Gate C authority request and is not acceptance.

## Withheld Authority

No threshold fitting, candidate retry, model load/inference, optimizer, new
decode, Gate C execution, policy selection/promotion, hardware, external
compute, or Brev.
