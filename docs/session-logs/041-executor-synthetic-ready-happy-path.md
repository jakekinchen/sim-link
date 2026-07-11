# Executor Session 041 - Synthetic Ready Happy Path

**Date:** 2026-07-10 23:10:00 CDT

## Slice

Implement one smallest useful slice from brief 029: add a bounded
`synthetic_test_only` measured-inertial path that compiles to `status: ready`,
prove exact golden aggregate mass/COM/full inertia and stable ready identity,
and keep the checked-in real current-arm path truthfully blocked.

## Files Changed

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/041-executor-synthetic-ready-happy-path.md`

Unrelated dirty and untracked worktree paths were present before this slice and
were left untouched.

## Tests / Validation

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- Live synthetic ready path:
  `python scripts/robot_lab/write_measured_inertial_intake.py --intake tests/fixtures/robot_lab/measured_mass/synthetic_complete.json --output /tmp/.../synthetic-ready.json --require-ready`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

All passed except the intentional nonzero default real-path
`--verify --require-ready` check, which correctly failed closed with
`status = blocked_missing_measurements`.

## Reachability

Real product path:

`python scripts/robot_lab/write_measured_inertial_intake.py`

This slice is reachable through the shipping measured-inertial CLI without any
test-only harness replacing the product entrypoint. The bounded paths now are:

- default current-arm verify still reads the checked-in real artifacts and
  proves they remain blocked;
- passing `--intake tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`
  plus a non-repo `--output` path compiles the synthetic fixture through the
  same compiler module to `status: ready`;
- the synthetic path hard-refuses either checked-in real destination, so it
  cannot overwrite the tracked current-arm artifacts by accident.

## Evidence

- Synthetic fixture:
  `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`
  with explicit `status = synthetic_test_only` and identity
  `412825dfedd4c5b015b81a2f4d32d208e6d1dbd6de547a665a8f92005acf8388`.
- Synthetic live ready output identity:
  `9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d`.
- Synthetic golden aggregate mass:
  `4.5` kg.
- Synthetic golden aggregate COM in assembly frame:
  `[0.35, 0.283333333, 0.033333333]`.
- Synthetic golden full inertia about aggregate COM in assembly frame:
  `[[0.073625, -0.053025, 0.26218125], [-0.053025, 1.1719375, 0.0126125], [0.26218125, 0.0126125, 1.11475]]`.
- Reordered synthetic components/atoms/priors/measurements still compile to the
  same ready payload identity because the synthetic intake ref is semantic and
  path-independent:
  `synthetic_test_only://synthetic_complete`.
- Default real current-arm identities remained unchanged:
  intake `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
  and output `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`.
- Synthetic compilation to either checked-in real destination now fails closed
  with `Synthetic test-only compilation cannot write to checked-in real artifact destinations`.

## Step-9 Flags For Reviewer

- Please rerun the bounded synthetic CLI path and confirm the ready output is
  reachable only through an explicit synthetic fixture input plus a non-real
  output destination.
- Please confirm the default blocked current-arm identities remain unchanged and
  the real path is still non-ready.
- Please note this slice intentionally proves only the happy path; the broader
  negative matrix for exact-cover ambiguity, reused evidence, and invalid
  transform/inertia cases is still open.

## Next Suggested Slice

Keep T16.4 open and implement the remaining synthetic negative matrix from the
active brief family: exact-cover ambiguity, reused-evidence rejection, and
invalid transform/inertia rejection, while preserving the default blocked real
artifact path and the path-independent synthetic semantic identity.
