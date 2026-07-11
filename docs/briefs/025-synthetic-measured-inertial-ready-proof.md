# Slice Brief 025 - Synthetic Measured Inertial Ready Proof

**Date:** 2026-07-10

## Objective

Finish the remaining T16.4 offline capability by adding a `synthetic_test_only`
measured-mass intake fixture and compiling it to a deterministic `ready`
assembly inertials result. The default current-arm artifact path must remain
truthfully blocked.

## Product / Project Value

This closes the math and fail-closed proof for T16.4 without inventing physical
SO-101 measurements. M16 can then carry a truthful blocked real arm plus a
separate verified synthetic proof that the compiler is ready for future real
measurements.

## Acceptance Criteria

- Add a synthetic intake fixture with multiple components, nonzero translation,
  and non-identity rotation. It must be explicitly labeled
  `synthetic_test_only` and must never become the default production input.
- Extend `scenesmith.robot_lab.measured_inertial_intake` so a complete measured
  synthetic fixture can compile to `status: ready` with deterministic aggregate
  mass, assembly-frame COM, and assembly-frame inertia about COM.
- Prove CAD inertia scaling by trusted measured mass, rotation into assembly
  frame, parallel-axis translation, mass-weighted COM aggregation, and summed
  assembly inertia against golden values.
- Reject invalid or ambiguous input: CAD-only coverage, missing required atoms,
  duplicate/overlapping/parent-child coverage, reused evidence, invalid mass,
  invalid transforms, nonpositive source mass, non-PSD inertia, and triangle
  inequality failures.
- Verify tamper/staleness checks fail for dependency-lock, TwinProfile,
  structural diff, intake linkage, and evidence references where applicable to
  the synthetic path.
- Preserve the current real CLI semantics:
  `python scripts/robot_lab/write_measured_inertial_intake.py --write-intake`
  still regenerates the blocked real artifacts, `--verify` still passes on the
  tracked blocked files, and `--require-ready` still fails nonzero for them.
- Prove input-order invariance and deterministic serialized identity for the
  synthetic ready artifact.

## Expected Files

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`
- `docs/session-logs/039-executor-*.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Test Plan

- Focused unit tests for synthetic ready compilation and blocked real-artifact
  preservation.
- Negative tests for overlap, duplicate evidence, missing coverage, invalid
  transforms/masses/inertias, and stale linkage.
- Order-invariance tests for component and measurement ordering.
- CLI tests for the default blocked real path and any bounded synthetic verify
  path added for testability.

## Validation Commands

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --write-intake`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

## Evidence To Record

- Synthetic fixture path and its semantic label proving it is not production
  evidence.
- Golden ready artifact mass/COM/inertia values and ready identity hash.
- Confirmation that the checked-in blocked real artifacts still verify at
  intake identity `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
  and output identity `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`.
- Negative-test evidence for overlap / tamper / stale-linkage rejection.

## Reachability / Demo Proof

The executor must show both paths:

- The real current-arm CLI remains blocked and truthful.
- The synthetic fixture reaches `ready` through the same compiler logic or a
  tightly bounded test-only entrypoint that cannot replace the default real
  artifacts by accident.

## Cross-Doc Impact

- Keep `GOAL.md` and the experience-compiler ledger aligned with T16.4 staying
  `in_progress` until the synthetic proof lands.
- Do not reopen T16.3 or change M17+ planning in this slice.

## Out Of Scope

- Any real physical measurement intake.
- Any hardware census, calibration, motion, or qualification work.
- Any training, optimizer, or experience-compiler work outside T16.4.
- Any unrelated cleanup in the already-dirty worktree.

## Stop Conditions

- Stop if the implementation would relabel CAD/MJCF priors as measured evidence.
- Stop if the synthetic path can overwrite or become the default current-arm
  production artifact.
- Stop if validation requires hardware, new external spend, or training.
