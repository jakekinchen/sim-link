# Executor Session 024 - pin robotics dependencies

**Date:** 2026-07-10

## Slice

Complete T16.1 by emitting one tracked robot-lab dependency lock that pins the
active LeLab runtime input, the separate dirty local LeRobot checkout, the
current Robot Studio SO-101 runtime files, and unresolved upstream references
for OpenPI and MuJoCo Menagerie without switching the runtime model.

## Files Changed

- `scenesmith/robot_lab/robotics_dependency_lock.py`
- `scripts/robot_lab/write_robotics_dependency_lock.py`
- `configurations/robot_lab/pi05_robotics_dependency_lock.json`
- `tests/unit/test_robotics_dependency_lock.py`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Tests / Validation

- `python -m py_compile scenesmith/robot_lab/robotics_dependency_lock.py scripts/robot_lab/write_robotics_dependency_lock.py`
- `python -m unittest tests.unit.test_robotics_dependency_lock`
- `python scripts/robot_lab/write_robotics_dependency_lock.py`
- `python scripts/robot_lab/write_robotics_dependency_lock.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

Additional evidence:

- `./.mujoco_venv/bin/python -m unittest tests.unit.test_robotics_dependency_lock tests.unit.test_pi05_autolearn`
  reached 36 passing tests and 1 unrelated environment failure:
  `ModuleNotFoundError: No module named 'lerobot'` in the pre-existing
  `build_pi05_provenance` coverage path.

## Reachability

The lock captures the exact runtime files used by the real robot-lab product
path today:

- `scenesmith.robot_lab.spec.RobotLabRobot.source_mjcf` resolves to
  `external/SO-ARM100/Simulation/SO101/so101_new_calib.xml`.
- `scenesmith.robot_lab.spec.RobotLabRobot.source_urdf` resolves to
  `external/leLab/frontend/public/so-101-urdf/urdf/so101_new_calib.urdf`.
- `scripts/robot_lab/write_robotics_dependency_lock.py --verify` re-reads the
  checked-in manifest and proves those active files, the LeLab `lerobot@v0.6.0`
  pin, and the dirty local `external/lerobot` patch identity are all reachable
  from the current repo state.
- The broader `test_robot_lab_scene_builder` pass proves the same MJCF/URDF
  contract remains load-bearing in the export path.

## Evidence

- Checked-in manifest:
  `configurations/robot_lab/pi05_robotics_dependency_lock.json`
- Active LeLab runtime:
  `external/leLab` at `def3e9e51e99c03e01b214dc8a0d9b7c2dd5f0da`,
  dirty only by untracked `uv.lock`, with runtime `lerobot` pinned to `v0.6.0`.
- Separate local LeRobot checkout:
  `external/lerobot` at `e40b58a8dfa9e7b86918c374791599d070518d11`,
  dirty in `src/lerobot/policies/pi05/modeling_pi05.py` and
  `src/lerobot/scripts/lerobot_train.py`, with tracked diff hash
  `efe912e3cf75c76a3b0a01d2baec8f0856ce2e2a981f4845978f0e9e34155284`.
- Active Robot Studio model:
  `external/SO-ARM100` at `fda892cba81032c46c40976a48c9ceadbf40a9ca`,
  clean, with active MJCF hash
  `d75253eb568e8a7214db9c631ab7bed4217f608a26f7276ebe9a7636cac82580`.
- Active URDF hash:
  `443d38d756e01bac7d3455b24430047ddc6427105e0d3454b2003116f5f67236`.
- OpenPI and Menagerie are recorded explicitly as unresolved upstream semantic /
  lineage references rather than falsely claimed as local pinned checkouts.
- Unrelated worktree changes outside this slice were left untouched.

## Step-9 Flags For Reviewer

- The slice intentionally does not resolve OpenPI or Menagerie to local
  checkouts; it records them as unresolved upstream references because the repo
  does not currently vendor either dependency.
- The broader `test_pi05_autolearn` environment still lacks an importable
  `lerobot` package for its existing provenance subtest. That failure is
  adjacent validation debt, not a regression from this slice.
- No runtime model, processor, coordinate contract, camera contract, training
  path, or hardware path was switched in this slice.

## Next Suggested Slice

Implement T16.2 by defining `TwinProfile`, `TwinQualificationSpec`, and
`TwinQualificationReport` schemas plus a simulation-only example that points
back to `pi05_robotics_dependency_lock.json`.
