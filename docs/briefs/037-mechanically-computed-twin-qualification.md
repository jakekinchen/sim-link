# Slice Brief 037 - Mechanically Computed Twin Qualification

**Date:** 2026-07-11

## Objective

Complete T16.2b by replacing caller-declared metric status with a versioned
qualification-evidence input, a deterministic report generator that computes
each result from the pinned specification, and an independent verifier that
recomputes the result. Feed scoped capability claims to the central authority
composer without allowing any profile, input, or report to grant global state.

## Required contracts

- Bind the exact signed TwinProfile and TwinQualificationSpec identities,
  dependency-lock identity, subject, scope, proof/evidence mode, run identity,
  evaluation time, and declared validity interval.
- Each metric input names the spec metric, exact units or a versioned explicit
  conversion, finite sample values, exact sample count, nonempty unique held-out
  trajectory IDs, content-addressed evidence, environmental conditions, and
  uncertainty or confidence information.
- The specification declares the aggregation and comparison rule. The generator
  derives the aggregate, conservative uncertainty-adjusted decision value,
  tolerance comparison, status, and stable reason codes. The caller supplies no
  `pass` or `fail` field.
- The verifier independently revalidates every reference and evidence identity,
  recomputes every derived value and status from raw inputs plus the spec, and
  rejects any drift in the serialized report.
- Missing required metrics become explicit `not_run`/withheld results only when
  the requested proof state permits that; they can never be inferred as pass.
- Fixture, synthetic, simulation, replay, and physical evidence modes remain
  distinct. Fixture evidence proves the computation path but cannot impersonate
  a physical run or establish physical qualification.

## Authority integration

- Qualification artifacts expose only scoped claims such as computation-valid,
  required-simulation-metrics-passed, or required-physical-metrics-passed.
- The central composer remains the only path for
  `simulation_training_ready`, `physical_transfer_ready`, and
  `promotion_eligible`.
- A TwinProfile cannot pre-authorize the report that evaluates it. Unknown or
  forged global-authority fields are rejected.
- The checked-in fixture composition must continue to withhold every global
  decision; `training_lock` remains closed.

## Adversarial acceptance

- Reject caller-declared status, status/tolerance disagreement, non-finite
  samples or derived values, zero/mismatched sample counts, missing/duplicate
  held-out IDs, wrong units, undeclared conversion, invalid environmental
  conditions, missing uncertainty/confidence, and expired validity.
- Reject stale profile/spec/dependency references, duplicate/reused evidence,
  content substitution, wrong subject/scope, fixture-to-physical relabeling,
  unauthorized issuer, and input-order nondeterminism.
- Reject a resigned report whose aggregate, uncertainty bound, comparison,
  status, reason code, or capability claim differs from independent
  recomputation.
- Preserve deterministic identities under semantically irrelevant input order.

## Validation

- Focused generator/verifier and authority-integration suite.
- Existing twin-contract, authority-composer, artifact-contract, measured-
  inertial, production-inertial, structural-twin, dependency-lock, and LeRobot
  regression gate.
- Checked-in fixture and composer product verifiers.
- `py_compile` and `git diff --check`.

## Out of scope

Hardware access, camera access, live bus construction, optimizer work, physical
calibration, actuation, physical qualification, transfer, deployment, and
promotion.

## Authority after this slice

If reviewed and remotely preserved, this may establish only
`twin_qualification_computation_valid` on declared fixture evidence. Any
simulation or physical metric capability remains scoped to its exact evidence
mode and is only an input to the central composer. No global decision is granted
by this slice.
