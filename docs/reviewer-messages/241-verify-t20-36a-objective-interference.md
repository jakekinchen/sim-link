# Reviewer Decision 241 - Verify T20.36a Objective Interference

**Decision:** `VERIFY_WEIGHTED_OBJECTIVE_NOT_GATE_EQUIVALENT_ROUTE_RETENTION_CONTRACT`

## Reviewed Boundary

Brief 192; signed X result `e79dacff...`; signed T20.36 result `02b543be...`;
all seven pinned input files; implementation, tests, CLI, signed audit
`339a7229...`; implementation commit `3bbdc64`; and the complete scoped diff.

## Adversarial Findings

- The audit verifies signed identities plus byte hashes for both specs, runs,
  results, and the unchanged threshold artifact. No checkpoint tensor is read.
- All 500 standard, weighted-correction, total, and pre-clip gradient rows are
  finite, complete, and recomputed into twenty fixed 25-update windows.
- T20.36's standard objective is `12.118449` times X. Its raw correction is
  `1.545902` times X and worst decoded error is `4.176295` times X. Every seed's
  maximum and mean action error worsens.
- The joint-weighted correction objective nevertheless improves to `0.513119`
  of X. The declared classification therefore follows mechanically: the
  weighted mean was not equivalent to the physical maximum-error gate under
  coverage training.
- Coverage loss holds 97.23%-99.07% of scalar objective mass in every fixed
  window and 420/500 combined gradients exceed the 1.0 pre-clip threshold.
  These are scale observations, not proof of individual-gradient conflict;
  the signed audit states that limitation explicitly.
- Stale identities, threshold drift, missing or non-finite histories,
  inconsistent decoded rows, classification tamper, and authority escalation
  fail closed. Twenty relevant tests pass; lint and exact verification pass.
- No model, inference, optimizer, rollout, gate change, hardware, external
  compute, or Brev action occurred.

## Disposition

Verify T20.36a. Open Brief 193 to encode the actual unchanged Gate B
conjunction as a pure checkpoint-retention contract. This decision grants no
future evaluation or training attempt; any such action requires a separate
owner/reviewer boundary.
