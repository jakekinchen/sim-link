# Slice Brief 015 - Quaternion And Solver Semantics

**Date:** 2026-07-10

## Objective

Advance T16.3 by correcting two semantic-false-diff sources in the structural
twin artifact: equivalent quaternion spelling and absent-versus-default MuJoCo
solver settings. Do not start inferred-inertia, friction/contact attachment, or
measured-mass work in this slice.

## Why This Slice Exists Now

- Brief 014's TwinProfile-binding correction is now proven by commit `936dd2f`.
- The next highest-value semantic gap is that the current diff still compares
  raw quaternion vectors and treats a missing `<option>` block as no solver
  evidence, which can misclassify semantically equivalent runtime state.
- T16.4 must stay blocked until T16.3 regains reviewer acceptance.

## Required Changes

- Canonicalize compared quaternions to unit length with one deterministic sign
  so scale/sign-equivalent rotations compare as matched.
- Preserve provenance-friendly raw values where useful, but record the compared
  canonical rotation values in the artifact for mismatched quaternion fields.
- Compare effective solver settings even when one model omits `<option>`, using
  documented MuJoCo defaults rather than treating omission as absence.
- Keep explicit `adopt`, `adapt`, or `retain` decisions on any true mismatch.
- Leave inferred-inertia unknown handling, effective friction/contact
  attachments, and deterministic unnamed-geom limitations for later briefs.

## Expected Files

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/NNN-executor-*.md`

## Tests And Verification

- Add focused tests for scale/sign-equivalent quaternion cases.
- Add focused tests that prove effective solver defaults compare even when one
  source omits `<option>`.
- Retain a regression that keeps true deltas such as `joint:wrist_roll` and
  `site:gripperframe` visible.
- Run:
  - `python -m unittest tests.unit.test_structural_twin_diff`
  - `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
  - `python scripts/robot_lab/write_structural_twin_diff.py`
  - `python scripts/robot_lab/write_structural_twin_diff.py --verify`
  - `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Evidence Required

- Scoped commit for this slice only.
- Updated artifact identity for the checked-in structural diff.
- Executor log that states exactly which T16.3 semantic gaps were closed and
  which remain open.
- Reachability proof from `scripts/robot_lab/write_structural_twin_diff.py`.

## Out Of Scope

- Measured-mass intake or assembly inertia compilation.
- Hardware access, read authority, motion authority, or Brev usage.
- Friction/contact attachment semantics beyond preserving current behavior.
- Inferred-inertia `unknown` representation beyond documenting it as remaining.

## Exit Condition

A fresh reviewer can confirm that equivalent quaternion spelling no longer
creates false mismatches and that solver-setting comparisons reflect effective
runtime defaults rather than XML omission alone, while T16.3 remains open for
the remaining semantic categories.
