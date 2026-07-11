# Reviewer Decision 043 - Central Authority Composition Reviewed

**Date:** 2026-07-11

## Decision

`CONTINUE T16.4b AFTER REMOTE PRESERVATION`

## Review target

Implementation commit `c0b96291e27c5612016d9451b6cbc8f3b5c320e9` under
Brief 034.

## Findings

- The versioned contract fixes stable prerequisite IDs and an acyclic `all`
  expression graph for `simulation_training_ready`, `physical_transfer_ready`,
  and `promotion_eligible`.
- Positive claims bind content-addressed evidence to subject, scope, provenance,
  validity/freshness, and a code-pinned issuer identity. Unknown, duplicate,
  contradictory, cyclic, ambiguous, stale, expired, not-yet-valid,
  unauthorized, substituted, and mismatched inputs fail closed.
- Component payloads carrying global-authority fields cannot be consumed. The
  legacy measured-inertial global gates now always reject and route callers to
  the central composer.
- `scenesmith.assembly_inertials.v2` exposes local capability facts only. The
  checked-in current arm remains blocked without measurements.
- Deterministic fixture compositions are explicitly non-authorizing. The review
  added this boundary after finding that a future complete fixture claim set
  otherwise needed a separate mechanical denial independent of provenance.
- Output records evaluated expressions, satisfied and missing prerequisites,
  denial codes, consumed evidence identities, request identity, contract
  identity, and composition identity. Claim ordering does not alter identity.

## Evidence

- 101-test broad gate passed in 46.653 seconds across the authority composer,
  artifact contract, measured inertials, twin contract, structural twin,
  LeRobot stack, and dependency lock.
- Composer, measured-inertial, twin, structural-twin, and LeRobot-stack product
  verifiers exited zero.
- Static imports and `git diff --check` passed.
- Contract identity:
  `6d04b20547a9391c4e695b5a337ee292410a2a13a8a3efdf34cb7033feda6ba1`.
- Denied composition identity:
  `d1206c5c710a280e4f7c5c448fd9ba59793b9850c2e9fd1bf962999ec82bc8ab`.

## Authority

The slice may establish `authority_composition_contract_valid` only after
remote preservation. It does not grant simulation training, physical
qualification, physical transfer, deployment, promotion, or optimizer
authority. `training_lock` remains closed.

## Pending gate

Remote preservation of the implementation and this reviewer decision must be
confirmed before T16.2b-A is marked verified or Brief 033 resumes.
