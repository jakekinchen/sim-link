# Reviewer Decision 199 - Verify T20.35 Rank-Capacity Result

**Decision:** `ACCEPT_VERIFIED_NEGATIVE_ROUTE_T20_35A_COVERAGE_AUDIT`

## Reviewed Evidence

Brief 166, Reviewer 198, the signed attempt, complete run summary, adapter
checkpoint tree/config, 500 objectives, 500 gradient norms, five decoded
chunks, frozen T20.33 comparison, signed result, tests, and remotely preserved
implementation `fd9399d` were reviewed together.

## Findings

- Exactly one counted attempt exists. The earlier Python 3.14 config rejection
  occurred before the signed marker, model construction, and optimizer and is
  correctly retained as pre-attempt runtime evidence rather than a retry.
- The counted attempt used rank/alpha 16, learning rate 2.5e-5, 500 updates,
  the frozen batch, training seed, five inference seeds, and unchanged gates.
- All 500 objectives and gradient norms are finite. The checkpoint tree and
  saved adapter rank, alpha, and target-module regex verify exactly.
- Objective ratio improves from rank 4's 0.528248 to 0.155307 but fails the
  required 0.10. All five decoded maximum errors fail 0.05 rad.
- The result is a Gate B failure, not policy acceptance or Gate C evidence.
- Hardware, cameras, serial devices, external compute, Brev, transfer, and
  promotion remain untouched or closed. User-owned dirty paths remain excluded.

## Disposition

Accept T20.35 as verified negative. Do not retry, continue, or run a broader
campaign. Open T20.35a as an optimizer-free audit that enumerates actual
PEFT-wrapped module names, trainable tensors, and saved adapter keys, with
explicit checks for action-expert input/output projections, action-time MLP,
and state projection. Another optimizer rung requires a separate brief and
central authority after the coverage and attainable-loss-floor evidence.
