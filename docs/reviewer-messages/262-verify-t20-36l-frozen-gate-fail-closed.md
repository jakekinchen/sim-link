# Reviewer Decision 262 - Verify T20.36l Frozen Gate Fail-Closed Result

**Decision:** `VERIFY_FROZEN_GATE_ACT_FAIL_SMOLVLA_INDETERMINATE`

## Reviewed Boundary

Brief 205; owner decision `32d7e193...`; frozen gate `463477dc...`; retained
scoring `0f8ae393...`; implementation
`e4c00bdbf0f0262b41d799f91b90cded94d7d8a2`; exact verifier; retained run
inventories; ACT localization witnesses; SmolVLA hashes/aggregates; 30 focused
and pointer tests; origin parity; and the complete scoped diff.

## Findings

- The owner decision freezes the T20.36k matrix before candidate scoring and
  retains objective ratio 0.10, deterministic repeats, all joint/timestep
  coverage, strict uniform 0.05-rad reporting, and the Gate C arbiter.
- ACT conclusively fails the amendment: shoulder lift error 0.125317 exceeds
  reach 0.05 at t0; wrist roll 0.442487 exceeds reach 0.4 at t0; gripper
  0.241636 exceeds grasp 0.025 at t49.
- SmolVLA's five pairs of action hashes match and its objective ratio passes,
  but neither standalone nor embedded 50x6 decoded tensors exist in the
  retained run. Aggregate maxima cannot identify phase or joint, so amended
  scoring is indeterminate and fails closed.
- The inventory lists checkpoint weights but does not read them. No model was
  constructed/loaded, no inference or new decode occurred, and Gate C,
  selection, acceptance, hardware, external compute, and Brev remain false.
- Original ACT and SmolVLA negative results remain visible and unchanged.

## Disposition

Verify T20.36l. ACT is closed. SmolVLA has not passed amended Gate B. Brief 206
is a proposed inference-only tensor-reproduction slice and remains pending an
exact owner authorization; this decision does not grant it. If later granted,
all five existing hashes must reproduce before frozen scoring, and any pass
routes only to separate Gate C authority.

## Withheld Authority

No model construction/load, inference, new decode, optimizer, threshold change,
Gate C execution, policy selection/promotion, hardware, network, external
compute, or Brev.
