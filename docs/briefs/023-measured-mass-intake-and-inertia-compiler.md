# Slice Brief 023 - Measured Mass Intake And Inertia Compiler

**Date:** 2026-07-10

## Objective

Complete T16.4 by compiling measured-part mass intake plus assembly inertia/COM
evidence against the verified T16.3 v2 structural baseline and current
simulation-only twin contract, without opening hardware or claiming physical
qualification.

## Why This Slice Exists Now

T16.3 is now reviewer-verified through commit `cadc0f3` and structural artifact
identity `fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9`.
The next blocker for M16 is no longer semantic structural honesty. The
remaining offline prerequisite is a deterministic, fail-closed path that turns
explicit measured-mass evidence into a content-addressed assembly inertia/COM
artifact that later T16.5 and T19.5 work can consume without guessing.

## Acceptance Criteria

- A checked-in artifact records measured-part mass inputs, evidence provenance,
  assembly membership, aggregate mass, center of mass, and compiled inertia
  outputs for the current simulation-only twin baseline.
- The compiler binds its output to:
  - `configurations/robot_lab/pi05_robotics_dependency_lock.json`
  - `configurations/robot_lab/pi05_twin_profile.simulation_only.json`
  - `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- The artifact records the accepted structural diff identity
  `fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9`.
- Missing, duplicated, ambiguous, or internally inconsistent mass evidence
  fails closed with explicit errors rather than guessed values.
- The artifact reports coverage explicitly: measured, excluded, unknown, and
  rejected components.
- Focused tests prove parallel-axis aggregation, aggregate COM composition, and
  fail-closed handling for incomplete or conflicting evidence.
- A repo-state CLI writes and verifies the artifact deterministically.
- Broader robot-lab validation still passes.

## Expected Files

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- One checked-in artifact under `configurations/robot_lab/`
- `docs/session-logs/NNN-executor-*.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Required Tests

- Deterministic unit tests for parallel-axis aggregation and aggregate COM math.
- Negative tests for missing measurements, duplicate part assignment, and
  conflicting evidence payloads.
- A determinism proof that repeated write/verify runs produce identical artifact
  content.

## Validation Commands

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_structural_twin_diff tests.unit.test_robot_lab_scene_builder`

## Evidence The Executor Must Record

- The artifact path and identity hash.
- The exact dependency-lock, TwinProfile, and structural-diff identities
  consumed.
- The measured-mass source paths or checked-in fixture inputs used.
- The coverage summary: measured, excluded, unknown, and rejected components.
- Focused and broad validation results.
- Reachability proving the artifact comes from repo-state inputs rather than a
  handwritten output.

## Reachability Rule

The slice is not done unless a real repo-local CLI consumes explicit measured
mass evidence plus the verified T16.3 baseline and emits or verifies the
checked-in assembly artifact deterministically. T16.5 and T19.5 must be able to
treat that output as the declared mass/inertia evidence source.

## Out Of Scope

- Opening hardware, reading the physical bus, or claiming M19 qualification.
- Editing runtime MJCF, Menagerie sources, or the verified T16.3 structural
  baseline beyond verifying their identities as inputs.
- T16.5 fake-bus identification and qualification harness work.
- Any scene-generation, asset-pipeline, prompt, or training changes already
  present elsewhere in the dirty worktree.

## Stop Conditions

- Stop if required mass or inertia evidence is missing from repo state and
  would require guessed or fabricated values.
- Stop if the compiler needs to alter the verified structural baseline instead
  of consuming it.
- Stop if the slice drifts into physical identification, motion, or contact
  qualification semantics.
