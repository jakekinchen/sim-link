# Executor Session 039 - Embedded Prior Integrity Correction

**Date:** 2026-07-10 21:20:00 CDT

## Slice

Implement one smallest useful slice from brief 026 Part A: harden the blocked
real measured-mass intake verifier so re-signed nested CAD-prior tampering and
duplicate component IDs fail before `build_assembly_inertials` can compile even
the diagnostic blocked output.

## Files Changed

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/039-executor-embedded-prior-integrity.md`

Unrelated dirty and untracked worktree paths were present before this slice and
were left untouched.

## Tests / Validation

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --write-intake`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

All passed except the intentional nonzero `--require-ready` check, which still
correctly rejected the blocked real artifact.

## Reachability

Real product path:

`python scripts/robot_lab/write_measured_inertial_intake.py --verify`

This CLI reads the tracked current-arm intake from
`configurations/robot_lab/pi05_measured_mass_intake.awaiting_measurements.json`
and routes through `verify_measured_mass_intake()` before verifying the blocked
assembly artifact. The strengthened verifier now requires deterministic equality
with a fresh repo rebuild, so a re-signed nested CAD-prior tamper fails on the
same production path that protects the checked-in artifact. The focused test
`test_write_assembly_inertials_refuses_forged_intake_without_output` also proves
that `write_assembly_inertials()` aborts before writing any output file when the
input intake has a forged `99` kg embedded prior.

## Evidence

- Re-signed `cad_priors[0].source_mass_kg = 99.0` now fails with
  `Measured mass intake drifted from deterministic repo rebuild`
- Duplicate component IDs now fail with
  `Duplicate measured mass intake component_id`
- A forged intake no longer produces any compiled output file
- Default CLI write/verify still preserves the tracked blocked identities:
  `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88` for the
  intake and `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`
  for the blocked assembly artifact
- The real arm remains `awaiting_measurements` / `blocked_missing_measurements`;
  no synthetic ready-state path was added in this slice

## Step-9 Flags For Reviewer

- Please rerun the forged-prior and duplicate-component regressions plus the
  live CLI `--verify` path to confirm nested evidence tampering now fails
  closed.
- Please confirm this slice intentionally covers only Part A of brief 026 and
  leaves Part B synthetic ready-state compilation for the next executor turn.
- Please confirm the stronger verifier did not change the checked-in real
  blocked artifact identities or claims.

## Next Suggested Slice

Keep T16.4 open and implement brief 026 Part B: a `synthetic_test_only` ready
fixture and compiler path with exact-cover measurement selection, hard-fail
overlap/reused-evidence checks, and golden mass/COM/inertia aggregation, while
leaving the default real-arm paths blocked.
