# Executor Session 037 - Canonical Unnamed Geom Identity V2

**Date:** 2026-07-10 19:25:10 CDT

## Slice

Implement the smallest useful T16.3 correction from brief 022: make unnamed collision-key hashing invariant to equivalent quaternion spellings and make same-stem duplicate occurrence assignment invariant to sibling order, without opening T16.4 or touching hardware/training paths.

## Files Changed

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

Unrelated dirty worktree paths were present before this slice and were left untouched.

## Tests / Validation

- `python -m unittest tests.unit.test_structural_twin_diff`
- `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

All passed.

## Reachability

Real product path:

`python scripts/robot_lab/write_structural_twin_diff.py`

This CLI imports `scenesmith.robot_lab.structural_twin_diff`, rebuilds the tracked artifact from the checked-in runtime MJCF, Menagerie source, dependency lock, and TwinProfile, and wrote:

- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`

Then:

`python scripts/robot_lab/write_structural_twin_diff.py --verify`

verified the tracked artifact against current repo state and source/profile hashes. That proves the v2 identity logic is reachable through the real artifact-generation path rather than tests alone.

## Evidence

- Identity strategy version: `scenesmith.structural_twin_diff.unnamed_geom_identity.v2`
- Tracked artifact identity: `fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9`
- Added focused regressions for:
  - equivalent scaled/sign quaternion spellings producing identical unnamed keys
  - reordered same-stem explicit-friction duplicates preserving collision/friction extraction
  - reordered same-stem class/inherited-friction duplicates preserving collision/friction extraction
- Implementation change scope:
  - canonicalize unnamed-geom identity payloads with shared quaternion semantics
  - sort same-stem duplicate groups by deterministic canonical full-attribute payload before suffix assignment
  - collapse signed zero during quaternion canonicalization so equivalent spellings hash identically

## Step-9 Flags For Reviewer

- Please rerun the two adversarial duplicate-order fixtures and the equivalent-quaternion fixture from `tests/unit/test_structural_twin_diff.py`.
- Please rerun `python scripts/robot_lab/write_structural_twin_diff.py --verify` independently and confirm the tracked artifact identity remains `fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9`.
- Please confirm T16.3 can now close and deferred brief 021 / T16.4 may resume only after that independent review.

## Next Suggested Slice

Do not implement a new product slice yet. The next action is reviewer re-audit for brief 022 and a fresh T16.3 decision. If accepted, resume deferred brief 021 for T16.4 measured mass intake and assembly inertia/COM compilation.
