# Executor Session 027 - twin contract schemas

**Date:** 2026-07-10

## Slice

Complete T16.2 by defining content-addressed `TwinProfile`,
`TwinQualificationSpec`, and `TwinQualificationReport` schemas, adding a real
write/verify CLI, and checking in one simulation-only, physically unqualified
example set bound to `configurations/robot_lab/pi05_robotics_dependency_lock.json`.

## Files Changed

- `scenesmith/robot_lab/twin_contract.py`
- `scripts/robot_lab/write_twin_contract_examples.py`
- `tests/unit/test_twin_contract.py`
- `configurations/robot_lab/pi05_twin_profile.simulation_only.json`
- `configurations/robot_lab/pi05_twin_qualification_spec.simulation_only.json`
- `configurations/robot_lab/pi05_twin_qualification_report.simulation_only.json`
- `GOAL.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Tests / Validation

- `python -m py_compile scenesmith/robot_lab/twin_contract.py scripts/robot_lab/write_twin_contract_examples.py tests/unit/test_twin_contract.py`
- `python -m unittest tests.unit.test_twin_contract`
- `python scripts/robot_lab/write_twin_contract_examples.py`
- `python scripts/robot_lab/write_twin_contract_examples.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Reachability

- `scripts/robot_lab/write_twin_contract_examples.py` is the real product path
  for this slice. It deterministically emits and verifies the checked-in twin
  profile, qualification spec, and qualification report artifacts from repo
  state.
- That script reaches
  `scenesmith.robot_lab.twin_contract.write_twin_contract_examples()` and
  `verify_twin_contract_examples()`, which bind all three artifacts back to
  `configurations/robot_lab/pi05_robotics_dependency_lock.json` by relative path,
  schema version, file hash, and identity hash.
- The broader `test_robot_lab_scene_builder` pass proves the existing robot-lab
  scene export path still imports and runs while the new twin-contract module
  and CLI are present.

## Evidence

- The checked-in simulation-only example set is:
  `configurations/robot_lab/pi05_twin_profile.simulation_only.json`,
  `configurations/robot_lab/pi05_twin_qualification_spec.simulation_only.json`,
  and `configurations/robot_lab/pi05_twin_qualification_report.simulation_only.json`.
- The example dependency-lock reference is
  `configurations/robot_lab/pi05_robotics_dependency_lock.json` with identity
  `222bce608b7c91527e1f37136ff97e1d2eeaeab59df384aeba2c98a511aff965`.
- The checked-in artifact identities are:
  `TwinProfile=4ec3884b43b79dbe17e3c5e86598a7641a24ec8f90872ac135c49e93a06c6ab5`,
  `TwinQualificationSpec=32eb1d353edc9db05f03b33dbd73d33e08d97bd9813d744d71e9596512fec995`,
  `TwinQualificationReport=fc1853656ab5ead8832417989151ae8acefa01a96ae99011142ec54ebfdedd63`.
- Validation rejects invalid parameter units/origins, reversed uncertainty
  bounds, missing dependency-lock linkage, stale identities, and invalid
  `physical_qualified` report combinations.
- Unknown physical measurements remain explicit unknowns instead of fabricated
  defaults in the inertial, friction/compliance, and camera/timing sections.
- Unrelated pre-existing worktree changes were left untouched.

## Step-9 Flags For Reviewer

- This slice introduces schemas and deterministic artifacts only; it does not
  reconcile Menagerie against Robot Studio yet and does not alter the active
  MJCF/URDF runtime inputs.
- The simulation-only report intentionally leaves physical metrics as `not_run`;
  `physical_qualified` remains unreachable without later M19 evidence.
- The repo worktree remains dirty in many unrelated files outside this slice;
  they were not staged or normalized here.

## Next Suggested Slice

Implement T16.3 by generating a machine-readable structural diff between the
active Robot Studio SO-101 runtime files and the pinned Menagerie
`robotstudio_so101` lineage, while preserving the current runtime inputs.
