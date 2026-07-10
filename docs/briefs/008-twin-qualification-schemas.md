# Slice Brief 008 - Twin Qualification Schemas

**Date:** 2026-07-10

## Objective

Complete T16.2 by defining durable schema types for the hardware twin profile,
qualification contract, and qualification result, plus one simulation-only
example bound to the robotics dependency lock.

## Product / Project Value

M16 needs a stable twin contract before structural reconciliation, measured-mass
ingest, or any compiler/training artifact can truthfully claim which simulated
robot it targets. This slice creates that contract without switching runtime
inputs or touching hardware.

## Acceptance Criteria

- A typed schema exists for `TwinProfile`.
- A typed schema exists for `TwinQualificationSpec`.
- A typed schema exists for `TwinQualificationReport`.
- One checked-in simulation-only example references
  `configurations/robot_lab/pi05_robotics_dependency_lock.json` by identity/path
  rather than copying loose assumptions into a new file.
- Validation rejects missing dependency-lock linkage, malformed proof-state
  values, and impossible qualification status/report combinations.
- The example stays explicit that it is simulation-only and unqualified for
  physical promotion.

## Expected Files

- `scenesmith/robot_lab/` schema module(s) for twin qualification
- `tests/unit/` coverage for schema creation and verification
- `configurations/robot_lab/` example twin-profile or qualification artifact
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/NNN-executor-*.md`

## Test Plan

- Add focused unit tests for valid construction and verifier rejection cases.
- Include at least one test that loads the checked-in simulation-only example and
  verifies it against the current dependency-lock artifact.
- Keep tests deterministic and offline.

## Validation Commands

- `python -m py_compile <new twin schema modules>`
- `python -m unittest <focused twin schema tests>`
- Any repo-local command used to emit or verify the example artifact
- One broader robot-lab validation command that proves the new schema package
  does not break existing import paths

## Evidence To Record

- The exact artifact path for the checked-in example
- The dependency-lock reference used by that example
- Focused validation results
- Broader validation result or a concrete non-regression explanation if a
  pre-existing environment issue remains outside the slice

## Reachability / Demo Proof

- Show where downstream M16-M19 work will consume the new schema types.
- Prove the committed example can be loaded and verified from the repo state as
  checked in.

## Cross-Doc Impact

- Mark T16.2 state and next step in
  `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`.
- Keep `GOAL.md` and the next executor log aligned with the new slice.

## Out Of Scope

- Reconciling Robot Studio against Menagerie
- Editing the active MJCF/URDF runtime contract
- Starting training or reopening M20 work
- Any physical robot read, write, or motion path

## Stop Conditions

- Stop if the schema design requires a human-owned policy decision about proof
  states or qualification semantics that is not already implied by `GOAL.md` and
  the milestone ledger.
- Stop if the slice would need to modify active runtime robot files rather than
  describe them.
