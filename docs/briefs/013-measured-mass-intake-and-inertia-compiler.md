# Slice Brief 013 - Measured Mass Intake And Inertia Compiler

**Date:** 2026-07-10

## Objective

Complete T16.4 by compiling measured-part mass intake plus assembly inertia/COM
evidence against the verified T16.3 structural baseline, without opening
hardware or claiming physical qualification.

## Product / Project Value

M16 cannot support a truthful hardware twin if later qualification work has to
guess masses, centers of mass, or inertia composition. This slice should create
one deterministic, fail-closed path that turns explicit measured-mass evidence
into an assembly-level artifact bound to the existing twin contract and
structural diff baseline.

## Acceptance Criteria

- A checked-in artifact records the measured-part mass inputs, declared evidence
  provenance, and compiled assembly inertia/COM outputs for the current
  simulation-only twin baseline.
- The compiler binds its output to both
  `configurations/robot_lab/pi05_robotics_dependency_lock.json` and
  `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`.
- Missing, duplicated, ambiguous, or internally inconsistent mass evidence
  fails closed with explicit error messages instead of guessed values.
- Assembly composition is deterministic and records which links or bodies were
  covered, excluded, or still unknown.
- Focused tests cover parallel-axis aggregation, COM composition, and the
  fail-closed cases for incomplete or conflicting evidence.
- A real CLI writes and verifies the artifact from repo state.
- Broader robot-lab validation still passes.

## Expected Files

- `scenesmith/robot_lab/` module(s) for measured-mass intake and inertia/COM
  compilation.
- `scripts/robot_lab/` CLI for writing and verifying the artifact.
- Focused unit tests under `tests/unit/`
- One checked-in artifact under `configurations/robot_lab/`
- `docs/session-logs/NNN-executor-*.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Test Plan

- Add deterministic unit tests for parallel-axis and aggregate COM math.
- Add negative tests for missing measurements, duplicate part assignments, and
  conflicting evidence payloads.
- Prove repeated write/verify runs produce identical artifact content.

## Validation Commands

- `python -m unittest <focused T16.4 test module>`
- `python <T16.4 write script>`
- `python <T16.4 write script> --verify`
- `./.mujoco_venv/bin/python -m unittest <focused T16.4 test module> tests.unit.test_robotics_dependency_lock tests.unit.test_structural_twin_diff tests.unit.test_robot_lab_scene_builder`

## Evidence To Record

- The artifact path and identity/hash.
- The exact structural-baseline and dependency-lock identities consumed.
- The mass-evidence source paths or checked-in fixture inputs used.
- The assembly coverage summary: measured, excluded, unknown, and rejected
  components.
- Focused and broad validation results.
- Reachability showing the artifact is generated from repo-state inputs rather
  than handwritten output.

## Reachability / Demo Proof

The slice is only done if a repo-state CLI consumes explicit measured-mass
evidence plus the verified T16.3 structural baseline and emits or verifies the
checked-in assembly artifact deterministically. T16.5 and T19.5 must be able to
consume this output as the declared mass/inertia evidence source.

## Cross-Doc Impact

- Update `GOAL.md` and `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
  only after the new artifact is verified.
- If the slice reveals that a required mass or inertia input cannot be produced
  offline from repo-state evidence, record that blocker explicitly instead of
  inventing placeholder measurements.

## Out Of Scope

- Opening hardware, reading the physical bus, or claiming any M19 qualification.
- Editing the active runtime MJCF, Menagerie sources, or the structural diff
  baseline beyond verifying their identities as inputs.
- Any scene-generation, asset-pipeline, prompt, or training changes already
  present elsewhere in the dirty worktree.
- T16.5 fake-bus identification and qualification harness work.

## Stop Conditions

- Stop if required mass or inertia evidence is missing from repo state and would
  need guessed or fabricated values.
- Stop if the compiler needs to change the verified structural baseline rather
  than consume it.
- Stop if the slice drifts into physical identification, motion, or contact
  qualification semantics.
