# Slice Brief 027 - Synthetic Measured Inertial Ready Closeout

**Date:** 2026-07-10

## Objective

Finish the remaining T16.4 work after commit `522457c`: keep the checked-in
current-arm artifacts truthfully blocked, and add a strictly synthetic,
`synthetic_test_only` proof path that demonstrates the ready-state measured
inertial compiler end to end.

## Current Truth

- Brief 026 Part A is complete: embedded CAD-prior tampering and duplicate
  component IDs now fail before blocked output compilation.
- The default real path still writes/verifies only
  `pi05_measured_mass_intake.awaiting_measurements.json` and
  `pi05_assembly_inertials.blocked_missing_measurements.json`.
- No synthetic fixture exists yet under
  `tests/fixtures/robot_lab/measured_mass/`.
- No bounded synthetic-ready CLI or test-facing compiler entrypoint exists yet.

## Acceptance Criteria

- Add `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`,
  explicitly labeled `synthetic_test_only`, with multiple components, nonzero
  translation, and a non-identity rotation.
- Extend `scenesmith.robot_lab.measured_inertial_intake` so a complete measured
  synthetic intake can compile to `status: ready` without ever becoming the
  default production input or writing to the tracked real-artifact paths.
- Enforce exact-cover measured selection for required atoms and reject missing
  atoms, duplicate active coverage, parent/child overlap, reused evidence,
  ambiguous assembly/frame mapping, and exclusions that hide required material.
- Reject CAD-only pseudo-measurements and invalid measurement provenance,
  uncertainty, mass, transforms, source mass, or inertia tensors.
- Prove CAD inertia scaling, assembly-frame rotation, parallel-axis
  translation, aggregate COM accumulation, and full summed inertia against
  deterministic golden values.
- Prove input-order invariance and stable semantic identity for the synthetic
  ready output.
- Preserve the current real-artifact CLI semantics:
  default write/verify still reproduces the blocked identities, and default
  `--require-ready` still exits nonzero.

## Expected Files

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`
- `docs/session-logs/040-executor-*.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Required Tests

- Positive ready-state test for the synthetic fixture with golden aggregate
  mass, assembly-frame COM, and full inertia.
- Negative tests for missing, duplicate, overlapping, parent/child, ambiguous,
  or reused-evidence coverage.
- Negative tests for CAD-only pseudo-measurement, invalid provenance fields,
  invalid mass/source mass, invalid transform shape, non-orthonormal or
  reflected rotation, nonfinite values, non-PSD inertia, and triangle-inequality
  violations.
- Order-invariance tests for component, prior, and measurement ordering.
- Regression tests showing the default real blocked path remains unchanged and
  `--require-ready` still rejects it.

## Validation Commands

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- Run the bounded synthetic-ready demo path and record the ready identity plus
  golden mass/COM/inertia outputs
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

## Evidence To Record

- Synthetic fixture path and its `synthetic_test_only` label.
- Golden ready aggregate mass, COM, and inertia values for the synthetic path.
- Ready artifact identity/hash for repeated-build invariance.
- Proof that the default blocked real identities remain:
  intake `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
  and output `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`.
- Negative-test evidence for exact-cover rejection, reused-evidence rejection,
  and invalid transform/inertia rejection.

## Reachability / Demo Proof

The executor must show both bounded paths:

- The real current-arm CLI remains blocked and unchanged.
- The synthetic fixture reaches `ready` through the same compiler logic or a
  tightly scoped test/demo entrypoint that cannot overwrite the tracked
  current-arm artifacts by accident.

## Out Of Scope

- Any real physical measurement intake.
- Any hardware census, actuation, calibration, or qualification work.
- Any M17+ experience-compiler, training, or optimizer work.
- Any unrelated cleanup in the already-dirty worktree.

## Stop Conditions

- Stop if the implementation would relabel CAD priors as measured evidence.
- Stop if the synthetic path can become the default current-arm input/output.
- Stop if validation requires hardware, external spend, or training.
