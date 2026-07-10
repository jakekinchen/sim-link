# Slice Brief 018 - Resume Inertial And Contact Truthfulness

**Date:** 2026-07-10

## Objective

Close the next truthful-semantics gap inside T16.3 by making the structural
twin diff report non-derivable inertials as explicit `unknown` evidence and by
separating effective friction/contact attachments from declaration-only
defaults.

## Product / Project Value

T16.3 cannot regain reviewer acceptance while the artifact still overclaims
what the available XML proves about inertial truth and contact behavior. This
slice restores honesty of representation before any measured-mass compiler or
training work can start.

## Acceptance Criteria

- Mass-bearing bodies whose inertia cannot be derived from the available source
  inputs land in `unknown`, not `matched`, `mismatched`, `missing`, or `extra`.
- The required Menagerie camera-mount inertial case is covered by a focused
  regression.
- Friction/contact comparison distinguishes effective runtime attachments from
  declaration-only defaults or unattached class records.
- Real effective friction/contact differences remain visible as true semantic
  deltas rather than being hidden by declaration-level records.
- The artifact preserves explicit `adopt`, `adapt`, or `retain` decisions for
  any mismatch, missing record, extra record, or surfaced unknown.
- Quaternion-clean categories stay clean; this slice must not reintroduce the
  five resolved collision-quaternion regressions.

## Expected Files

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/NNN-executor-*.md`

## Test Plan

- Add focused tests proving a non-derivable inertial case is emitted in
  `unknown`.
- Add the Menagerie camera-mount inertial regression.
- Add focused tests that differentiate effective friction/contact attachments
  from declaration-only defaults or unattached classes.
- Retain regressions that keep true effective friction/contact deltas visible.
- Keep existing quaternion regressions passing.

## Validation Commands

- `python -m unittest tests.unit.test_structural_twin_diff`
- `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Evidence To Record

- One scoped commit for this slice only.
- Updated structural-diff artifact identity.
- Executor log that states exactly which inertial/contact truthfulness gaps were
  closed and what still remains in T16.3.

## Reachability / Demo Proof

Prove the behavior through `scripts/robot_lab/write_structural_twin_diff.py`
with a sequential write and `--verify` run against the checked-in artifact.

## Cross-Doc Impact

- Update the T16.3 ledger entry and milestone log with the new artifact
  identity, validation counts, and remaining semantic limits.
- Keep `GOAL.md` aligned with the reduced T16.3 scope if this slice lands.

## Out Of Scope

- Deterministic unnamed-geom identifier repair.
- T16.4 measured-part mass intake or inertia/COM compilation.
- Hardware access, authority-gated work, or Brev usage.
- Any T17+ compiler or training activity.

## Stop Conditions

- Stop if the only way to classify an inertial/contact case would be to invent
  evidence not present in the pinned runtime or Menagerie sources.
- Stop if the slice would need to rewrite already accepted quaternion semantics
  instead of preserving them.
