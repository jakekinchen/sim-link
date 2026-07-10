# Executor Session 004 - dagger correction export

**Date:** 2026-07-10

## Slice

Add truthful policy-visited DAgger correction classification, dataset export
metadata, and pure-policy evaluation/promotion metrics.

## Files Changed

- `scenesmith/robot_lab/autolearn.py`
- `scripts/robot_lab/export_intervention_dataset.py`
- `tests/unit/test_pi05_autolearn.py`

## Tests / Validation

- `./.mujoco_venv/bin/python -m unittest tests.unit.test_pi05_autolearn tests.unit.test_robot_lab_intervention`
  passed 33 tests.
- Python compilation passed for the new library and exporter.
- The accepted V10 hybrid trajectory produced 660 DAgger correction frames
  from 3,219 source frames: 341 tray transfer, 109 recovery pick, and 210
  post-place frames. Mean policy/expert action delta was 0.5707476 radians.

## Reachability

`export_intervention_dataset.py --frame-selection dagger_corrections` now uses
the same trajectory artifacts produced by the live randomized policy path. It
retains policy proposals as sidecar evidence while training `action` targets on
the privileged action that was actually executed.

## Evidence

- Selection and promotion unit tests in `tests/unit/test_pi05_autolearn.py`.
- Accepted trajectory:
  `outputs/robot_lab/so101_desk_cube_sort/evals/v10-250-closedloop-hybrid-pregrasp-seed6204/randomized-episode-6204/intervention_trajectory.json`.

## Step-9 Flags For Reviewer

- Controller corrections are training-eligible only when the summary explicitly
  reports real neural actions, `scripted_object_motion=false`, and no physical
  follower command.
- Pure promotion currently treats any grasp-assist activation as assistance by
  default; a future config may explicitly allow contact-only friction assist.

## Next Suggested Slice

Implement the bounded cycle runner, Git manifest commits, training cleanup, and
held-out accepted-pointer update.
