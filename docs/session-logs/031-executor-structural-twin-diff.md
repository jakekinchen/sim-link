# Executor Session 031 - Structural Twin Diff

**Date:** 2026-07-10

## Slice

Complete T16.3 by emitting a deterministic, checked-in structural diff between
the active Robot Studio SO-101 runtime MJCF and the pinned Menagerie
`robotstudio_so101/so101.xml`, without switching runtime inputs or opening
hardware.

## Files Changed

- `scenesmith/robot_lab/structural_twin_diff.py`
- `scripts/robot_lab/write_structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `GOAL.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Tests / Validation

- `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py tests/unit/test_structural_twin_diff.py`
- `python -m unittest tests.unit.test_structural_twin_diff`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

All five focused structural-diff tests passed. The broad robot-lab suite passed
with 17 tests. The repo printed the existing `Mocking bpy due to import error:
No module named 'bpy'` test-environment message, but validation still completed
successfully.

## Reachability

The real product path for this slice is
`scripts/robot_lab/write_structural_twin_diff.py`. It resolves
`configurations/robot_lab/pi05_robotics_dependency_lock.json`, verifies the
dependency lock and both source-file hashes, parses the active runtime
`external/SO-ARM100/Simulation/SO101/so101_new_calib.xml` and pinned Menagerie
`third_party/mujoco_menagerie/robotstudio_so101/so101.xml`, and writes or
verifies the checked-in artifact from repo state. No hard-coded duplicate source
paths or handwritten diff payloads are used.

## Evidence

- Artifact: `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- Identity: `d71576574eb3dbb592cb495481a9de2e17e1581cc3e10476e1bc098106053b89`
- Source hashes proved before parse:
  - Runtime `external/SO-ARM100/Simulation/SO101/so101_new_calib.xml`
    `d75253eb568e8a7214db9c631ab7bed4217f608a26f7276ebe9a7636cac82580`
  - Menagerie `third_party/mujoco_menagerie/robotstudio_so101/so101.xml`
    `5ad49f2b45c083baac9ffe5d4d3213a5da7eac8039095bb2df177a697aae8308`
- Summary counts: 8 matched, 32 mismatched, 29 missing, 5 extra, 0 unknown.
- Recorded mismatches include:
  - `joint:wrist_roll` upper-limit delta `+0.097359009` radians on the runtime model.
  - `site:gripperframe` transform delta with position `[-0.0199, -1.21e-07, -4e-07]`.
  - Menagerie-only `camera:wrist_cam` and Menagerie-only `option:global` solver settings.
  - Menagerie-only gripper collision/contact geometry and runtime-versus-Menagerie actuator force-range differences.
- Every mismatched, missing, or extra record carries an explicit reconciliation
  decision (`retain` or `adapt`) so later M16-M19 work does not silently treat
  the two structures as equivalent.

## Step-9 Flags For Reviewer

- The diff engine normalizes numeric XML attributes, so equivalent formatting
  changes should not churn the artifact.
- Collision comparison is structural and deterministic, but it still compares
  per-geom encodings rather than a physics-equivalence reduction. That is
  intentional for T16.3 and should stay explicit in any follow-on review.
- The worktree contains many unrelated dirty and untracked files outside the
  robot-lab slice. They were left untouched.

## Next Suggested Slice

Start T16.4 by building a measured-part mass intake artifact and assembly
inertia/COM compiler that consumes this structural diff as the declared
baseline, with fail-closed behavior for missing or ambiguous mass evidence.
