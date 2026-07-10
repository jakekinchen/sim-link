# Executor Session 025 - finish portable dependency pins

**Date:** 2026-07-10

## Slice

Finish T16.1 by correcting the tracked robotics dependency lock so it pins exact
OpenPI and MuJoCo Menagerie revisions with license/content hashes and verifies
from equivalent checkout roots without embedding an absolute `repo_root`.

## Files Changed

- `scenesmith/robot_lab/robotics_dependency_lock.py`
- `tests/unit/test_robotics_dependency_lock.py`
- `configurations/robot_lab/pi05_robotics_dependency_lock.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Tests / Validation

- `python -m py_compile scenesmith/robot_lab/robotics_dependency_lock.py scripts/robot_lab/write_robotics_dependency_lock.py`
- `python -m unittest tests.unit.test_robotics_dependency_lock`
- `python scripts/robot_lab/write_robotics_dependency_lock.py`
- `python scripts/robot_lab/write_robotics_dependency_lock.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Reachability

- `scripts/robot_lab/write_robotics_dependency_lock.py` is the real product path
  that emits and verifies `configurations/robot_lab/pi05_robotics_dependency_lock.json`.
- That script reaches `scenesmith.robot_lab.robotics_dependency_lock.build_robotics_dependency_lock()`,
  which still derives the active MJCF and URDF from `RobotLabRobot.source_mjcf`
  and `RobotLabRobot.source_urdf`.
- The broader `test_robot_lab_scene_builder` pass proves the same robot-lab
  MJCF/URDF contract remains live in the product export path while the dependency
  lock now records portable exact upstream pins.

## Evidence

- OpenPI semantic reference is now pinned to
  `15a9616a00943ada6c20a0f158e3adb39df2ccac` with:
  `LICENSE`, `src/openpi/transforms.py`, and
  `src/openpi/shared/normalize.py` hashes recorded.
- Menagerie `robotstudio_so101` is now pinned to
  `71f066ad0be9cd271f7ed58c030243ef157af9f4` with:
  `robotstudio_so101/LICENSE`, `robotstudio_so101/README.md`, and
  `robotstudio_so101/scene.xml` hashes recorded.
- `identity_sha256` no longer signs an absolute checkout path.
- The relocation test builds equivalent nested git fixtures at two different
  roots and proves the generated payloads are identical and independently
  verifiable.
- Unrelated pre-existing worktree changes were left untouched.

## Step-9 Flags For Reviewer

- Menagerie remains a pinned structural lineage reference only; this slice does
  not switch the active runtime model to Menagerie.
- OpenPI remains a pinned semantic reference only; this slice does not claim the
  runtime executes OpenPI code directly.
- The repo worktree is already dirty in many unrelated files outside this slice;
  they were not staged or normalized here.

## Next Suggested Slice

Implement T16.2 by adding `TwinProfile`, `TwinQualificationSpec`, and
`TwinQualificationReport` schemas plus one simulation-only example that binds
back to `configurations/robot_lab/pi05_robotics_dependency_lock.json`.
