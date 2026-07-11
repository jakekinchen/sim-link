# Executor Session 035 - Inertial And Contact Truthfulness

**Date:** 2026-07-10

## Slice

Implement one T16.3 semantic-correction sub-slice by surfacing non-derivable
body inertials as explicit `unknown` evidence and by separating effective
friction/contact attachments from declaration-only default classes. This slice
does not reopen quaternion handling, measured-mass compilation, hardware, or
deterministic unnamed-geom repair.

## Files Changed

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `GOAL.md`

## Tests / Validation

- `python -m unittest tests.unit.test_structural_twin_diff`
- `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

Focused validation passed with 15 structural-diff tests. Broad validation
passed with 40 robot-lab tests. The suite printed the existing environment
message `Mocking bpy due to import error: No module named 'bpy'`, but no test
failed.

## Reachability

The real product path remains `scripts/robot_lab/write_structural_twin_diff.py`.
That entrypoint calls
`scenesmith.robot_lab.structural_twin_diff.write_structural_twin_diff`, which
now:

- emits an explicit inertial `unknown` record for the Menagerie
  `camera_mount` body because it carries geom mass but no derivable body
  inertial; and
- compares friction/contact through actual attached joints and collision geoms,
  while keeping unattached declaration-only defaults explicit in `unknown`
  instead of treating them as effective runtime behavior.

The sequential `write` then `--verify` run proves the updated behavior is
reachable from the tracked product entrypoint rather than from test-only
wiring.

## Evidence

- Commit: pending
- Artifact: `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- Structural diff identity: `fe9177e07a597e9db57c1896f5295f84b7ae9ff313219e33afa83b41c46fd08d`
- New regression proof:
  - `categories.inertials.unknown` now contains the Menagerie
    `body:base/shoulder/upper_arm/lower_arm/wrist/gripper/camera_mount` record
    with `mass: 0.012` carried by attached geom evidence;
  - declaration-only contact defaults are now emitted as `unknown` records with
    source-side provenance instead of as matched/missing/extra structural
    comparisons; and
  - effective contact differences now remain visible on attached collision
    records, with focused tests covering both declaration-only separation and a
    true attached friction delta.

## Step-9 Flags For Reviewer

- T16.3 remains open only for deterministic unnamed-geom limits.
- The worktree contains many unrelated modified and untracked files outside
  this robot-lab slice; they were left untouched.
- This slice intentionally increases friction `missing` counts because the
  artifact now reports real attached Menagerie gripper/camera contact records
  instead of collapsing contact evidence to class declarations.

## Next Suggested Slice

Close the remaining deterministic unnamed-geom limits in T16.3 without
changing the now-correct quaternion or inertial/contact truthfulness behavior.
