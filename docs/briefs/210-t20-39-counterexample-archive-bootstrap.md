# Brief 210 - T20.39 Counterexample Archive Bootstrap

## Status

Active model-free filler after Reviewer 278 verifies T20.38.

## Objective

Define a deterministic, versioned counterexample receipt/index contract and
bootstrap archive seed `0001` from T20.19's immutable `gripper_scale_high`
cell, honestly labelled `source_controller_boundary_negative` rather than a
policy failure or training sample.

## Required Contract

1. Bind the exact T20.19 cell manifest and scorecard gate, including source
   identities, cell id/factor/value, controller ownership, strict-v2 outcome,
   terminal outcome, replay determinism, and uncalibrated-grid scope.
2. Define a counterexample receipt with immutable id, semantic fingerprint,
   source refs, provenance class, capability stage, failure class, controller
   owner, task/object scope, predicate evidence, lifecycle state, routing,
   replay tier, and explicit authority withholding.
3. Define deterministic duplicate handling. One semantic fingerprint may have
   one active canonical receipt; exact duplicates are references, conflicting
   duplicates and path aliases fail closed.
4. Define lifecycle states and transitions for `active`, `superseded`,
   `retired`, and `invalid`. Stale/missing source evidence invalidates replay
   eligibility without deleting history.
5. Define a fail-closed routing matrix separating evidence-only archival,
   fixed-regression candidacy, compiler quarantine, policy-regression blame,
   replay-gate activation, and training-ingestion eligibility.
6. Seed archive/index `0001` as evidence-only. It may document a source
   controller boundary but cannot blame a learned policy, enter training,
   activate a replay gate, or imply calibrated robustness.

## Acceptance

- Exact schema/build/verify APIs and checked-in receipt/index reconstruct with
  stable identities.
- Tests cover duplicates, conflicting duplicates, aliases, stale/missing
  sources, lifecycle transitions, routing escalation, policy-blame guards,
  training/replay denial, deterministic ordering, and source drift.
- Seed `0001` binds T20.19's sole failing cell and retains its exact truthful
  label and terminal outcome.
- Focused and relevant regression tests, same-agent adversarial review,
  canonical records, scoped commit, push, and origin confirmation agree.

## Prohibited Actions

No simulation or policy replay, model action, optimizer, training ingestion,
replay-gate activation, policy blame without policy-owned evidence, source
rewrite, hardware, camera/serial access, network/download, external compute,
Brev, promotion, or destructive deletion.
