# Slice Brief 034 - Central Authority Composition Foundation

**Date:** 2026-07-11

## Objective

Complete T16.2b-A before extending the production measured-inertial compiler.
Introduce one fail-closed authority-composition contract that consumes scoped
component capabilities and evidence, evaluates machine-readable prerequisites,
and is the only code path allowed to grant system-level readiness.

## Architectural boundary

A component can establish facts local to itself. For example, an inertial
artifact may establish:

```json
{
  "capabilities": {
    "artifact_schema_valid": true,
    "inertial_compilation_valid": true,
    "inertial_model_usable_for_simulation": true,
    "physical_measurement_evidence_verified": false
  }
}
```

It must not grant `physical_twin_qualified`, `physical_transfer_ready`, or
`promotion_eligible`. Those are global decisions derived only by the central
composer.

## Required global decisions

The contract must represent stable prerequisite IDs and machine-readable
expressions for:

```text
simulation_training_ready
  = structural_contract_valid
  AND executable_stack_valid
  AND coordinate_contract_valid
  AND normalization_contract_valid
  AND experience_compiler_valid
  AND required_simulation_properties_available

physical_transfer_ready
  = simulation_training_ready
  AND physical_hardware_identity_verified
  AND actuator_and_timing_qualification_passed
  AND camera_qualification_passed
  AND contact_qualification_passed
  AND held_out_twin_metrics_passed

promotion_eligible
  = policy_artifact_and_training_provenance_valid
  AND appropriate_evaluation_tier_passed
  AND required_deployment_authority_present
  AND no_safety_or_proof_state_violation
```

## Acceptance criteria

- Define typed, versioned schemas for component capabilities, evidence claims,
  prerequisite expressions, composed decisions, denial reasons, and missing
  prerequisite IDs.
- Use stable capability and prerequisite identifiers. Reject unknown,
  duplicate, malformed, cyclic, or ambiguous expression inputs.
- Bind every positive capability to content-addressed evidence, scope,
  provenance class, subject identity, validity interval or freshness policy,
  and issuer/authority identity where required.
- Fail closed for missing, expired, stale, contradictory, synthetic-only,
  fixture-only, replay-only, unauthorized, or subject-mismatched evidence.
- Make the composer the only production API capable of emitting global
  readiness decisions. Component payload fields that overclaim global authority
  are rejected or ignored with an explicit denial; they can never be trusted.
- Produce deterministic canonical output with the evaluated expression,
  satisfied prerequisites, missing prerequisite IDs, denial reason codes,
  consumed artifact identities, and a composition identity.
- Keep positive readiness mechanically derived. Callers cannot pass a boolean
  or status that pre-authorizes the decision.
- Preserve safe compatibility where possible. If the existing schema cannot
  express the boundary without ambiguity, bump its version and regenerate
  deterministic fixtures explicitly.
- Amend Brief 033 and affected schemas before the production inertial output is
  extended, so inertial artifacts expose local capability facts only.
- Add adversarial tests for forged component authority, stale references,
  evidence substitution, subject mismatch, contradictory claims, synthetic or
  fixture evidence impersonating physical evidence, unknown prerequisites,
  missing prerequisites, duplicate claims, and nondeterministic input order.
- Prove that no adversarial component payload can independently cause
  `simulation_training_ready`, `physical_transfer_ready`, or
  `promotion_eligible` to become true.

## Validation

- Run the new focused authority-composer test suite.
- Re-run the artifact-contract, measured-inertial, twin-contract, structural
  twin, and LeRobot stack suites that feed or consume authority facts.
- Exercise at least one product-level CLI or verifier path showing explicit
  denial reasons for the current synthetic and blocked-real artifacts.
- Run `py_compile` or the repository's equivalent static import check on every
  touched Python module and `git diff --check` on the scoped diff.

## Out of scope

- Completing the production hierarchical inertial compiler.
- Computing TwinQualificationReport metric results.
- Opening hardware, running the T16.5 live census, optimizer training, paid
  compute, transfer qualification, or policy promotion.

## Authority after this slice

This slice may grant only `authority_composition_contract_valid`. It does not
grant simulation training, physical transfer, physical qualification,
deployment, promotion, or optimizer authority. `training_lock` remains closed.

## Stop conditions

- Stop and correct the design if any component artifact can grant a global
  decision directly.
- Stop and fail closed if evidence class, subject, scope, freshness, or issuer
  cannot be established mechanically.
- Do not weaken a prerequisite merely to make a fixture or current artifact
  pass.
