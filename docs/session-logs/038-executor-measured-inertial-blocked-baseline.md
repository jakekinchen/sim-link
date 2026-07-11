# Executor Session 038 - Measured Inertial Blocked Baseline

**Date:** 2026-07-10 20:31:00 CDT

## Slice

Implement the smallest useful T16.4 slice from brief 024: add the truthful
checked-in current-arm measured-mass intake and blocked assembly inertials
artifacts, plus the real CLI write/verify/require-ready path, without claiming
any synthetic ready-state proof or physical measurements.

## Files Changed

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `configurations/robot_lab/pi05_measured_mass_intake.awaiting_measurements.json`
- `configurations/robot_lab/pi05_assembly_inertials.blocked_missing_measurements.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

Unrelated dirty worktree paths were present before this slice and were left
untouched.

## Tests / Validation

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --write-intake`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

All passed except the intentional nonzero `--require-ready` check, which
correctly rejected the blocked real artifact.

## Reachability

Real product path:

`python scripts/robot_lab/write_measured_inertial_intake.py --write-intake`

This CLI imports `scenesmith.robot_lab.measured_inertial_intake`, regenerates
the tracked current-arm intake from repo evidence, compiles the default real
artifact, and wrote:

- `configurations/robot_lab/pi05_measured_mass_intake.awaiting_measurements.json`
- `configurations/robot_lab/pi05_assembly_inertials.blocked_missing_measurements.json`

Then:

`python scripts/robot_lab/write_measured_inertial_intake.py --verify`

re-verified both artifacts against the current dependency lock, TwinProfile,
structural diff, and intake file hash, while:

`python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`

failed nonzero because the real artifact truthfully remains
`blocked_missing_measurements`. That proves the blocked-state behavior is
reachable through the real artifact-generation path rather than tests alone.

## Evidence

- Intake identity: `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
- Blocked output identity: `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`
- CAD prior summary in the blocked artifact retains the seven runtime inertial
  masses as priors only, totaling `0.632006` kg
- The checked-in intake has status `awaiting_measurements`, an empty
  `measurements` list, required coverage atoms for the seven runtime structural
  bodies plus unresolved physical categories, and separate CAD prior records
- The checked-in output has status `blocked_missing_measurements`, null physical
  aggregate mass/COM/inertia, explicit missing coverage, and both
  `physical_qualification_authority` and
  `training_or_promotion_authority` set to `false`

## Step-9 Flags For Reviewer

- Please rerun the live CLI write/verify path and confirm the tracked intake and
  blocked output identities remain unchanged.
- Please confirm this slice intentionally does not implement the synthetic ready
  compiler yet, and therefore T16.4 remains `in_progress`.
- Please verify that the checked-in artifact language never relabels CAD/MJCF
  priors as measured physical evidence.

## Next Suggested Slice

Keep T16.4 open and implement the `synthetic_test_only` ready-state compiler
path next: measured coverage selection, CAD inertia scaling, rotated +
parallel-axis assembly aggregation, and hard-fail overlap/tamper checks, while
leaving the default current-arm artifact blocked.
