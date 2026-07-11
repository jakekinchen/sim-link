# Executor Session 040 - Measured Inertial CLI Path Safety

**Date:** 2026-07-10 22:05:00 CDT

## Slice

Implement one smallest useful slice from brief 028: repair the measured-inertial
CLI so caller-provided absolute intake/output paths outside the repo are
preserved instead of being forced through `Path.relative_to(REPO_ROOT)`, and
prove the external write/verify/fail paths directly through the product CLI.

## Files Changed

- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/040-executor-cli-path-safety.md`

Unrelated dirty and untracked worktree paths were present before this slice and
were left untouched.

## Tests / Validation

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`
- Live external-temp CLI path:
  `python scripts/robot_lab/write_measured_inertial_intake.py --write-intake --intake /tmp/.../external-intake.json --output /tmp/.../external-output.json`
- Live external-temp CLI verify:
  `python scripts/robot_lab/write_measured_inertial_intake.py --verify --intake /tmp/.../external-intake.json --output /tmp/.../external-output.json`
- Live external-temp CLI blocked ready check:
  `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready --intake /tmp/.../external-intake.json --output /tmp/.../external-output.json`
- Live external-temp invalid-input no-overwrite check:
  tamper the external intake, rerun
  `python scripts/robot_lab/write_measured_inertial_intake.py --intake /tmp/.../external-intake.json --output /tmp/.../external-output.json`

All passed except the intentional nonzero `--require-ready` and invalid-input
checks, which correctly failed closed.

## Reachability

Real product path:

`python scripts/robot_lab/write_measured_inertial_intake.py`

This is the shipping CLI for measured-mass intake and blocked assembly
compilation. The path-safety fix is exercised on the same entrypoint the user
or workflow would invoke by passing `--intake` and `--output` absolute paths
outside the repo. The live product flow now:

- writes an external blocked artifact successfully;
- verifies that same external artifact successfully;
- rejects `--require-ready` against that external blocked artifact with the same
  truthful non-ready status;
- rejects a tampered external intake before writing a new output, leaving the
  existing external output byte-for-byte unchanged.

## Evidence

- `_relative_to_repo()` now returns repo-relative paths only when an absolute
  path is actually under `REPO_ROOT`; outside-repo absolute paths remain
  absolute.
- Default tracked real path still verifies with the same blocked identities:
  intake `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
  and output `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`.
- Live external absolute write succeeded at
  `/var/folders/hm/6gd6d81d5wbfmk6j51dx894c0000gn/T/tmp.bWFQ29oVVl/`
  with output identity
  `e92738a2b9f450a72c693d67903eb75cbaa40a483a35c18f4a46cf09521e1478`.
- Live external absolute verify succeeded against the same output path and
  identity.
- Live external `--require-ready` exited nonzero with
  `status = blocked_missing_measurements`.
- After re-signing a forged external intake (`cad_priors[0].source_mass_kg =
  99.0`), the CLI failed with
  `Measured mass intake drifted from deterministic repo rebuild` before writing
  a new output.
- The forged external-input run preserved the existing external output
  byte-for-byte with unchanged file sha256
  `7fe752efca565caca826dbd1c12b052899b72235115cf7a3663eae9b1666b35e`.
- The real arm remains blocked; no `ready` path or physical measurement claim
  was added in this slice.

## Step-9 Flags For Reviewer

- Please rerun the four external absolute-path CLI regressions and confirm the
  fix is narrowly scoped to path normalization.
- Please confirm the default tracked current-arm identities remain unchanged and
  the real current-arm path is still blocked.
- Please confirm this slice intentionally does not attempt the synthetic ready
  compiler or any T16.5+ work.

## Next Suggested Slice

Keep T16.4 open and implement the remaining brief 028 work: add the
`synthetic_test_only` ready fixture and compiler path, prove golden aggregate
mass/COM/full inertia, and hard-fail exact-cover overlap, reused-evidence, and
invalid transform/inertia cases while keeping the default real-artifact paths
blocked.
