# Slice Brief 029 - Synthetic Ready Compiler Happy Path

**Date:** 2026-07-10

## Objective

Implement the next smallest useful T16.4 slice after the CLI path-safety fix:
add a bounded `synthetic_test_only` measured-inertial path that compiles to
`status: ready` and proves deterministic golden aggregate mass, COM, full
inertia, and stable ready identity.

## Product / Project Value

T16.4 cannot close until the compiler proves it can produce a truthful `ready`
artifact in an offline-only path. This slice establishes the positive synthetic
proof without relaxing the blocked real-arm boundary or opening hardware work.

## Acceptance Criteria

- Add `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`,
  explicitly labeled `synthetic_test_only`, with multiple components, nonzero
  translations, and a non-identity rotation.
- Extend `scenesmith.robot_lab.measured_inertial_intake` so the synthetic
  fixture can compile to `status: ready` through the same compiler logic or a
  tightly scoped test/demo entrypoint.
- Prove exact golden aggregate mass, assembly-frame COM, and full inertia for
  the synthetic path, including CAD inertia scaling, rotation into the assembly
  frame, transformed component COM, and parallel-axis summation.
- Prove repeated builds of the same synthetic input produce a stable ready
  identity, and that reordering the synthetic components/priors/measurements
  does not change the semantic result.
- The synthetic path must not become the default current-arm input/output path
  and must refuse either checked-in real-artifact destination.
- Default real-path write/verify semantics remain unchanged, and default
  `--require-ready` still exits nonzero against the blocked real artifact.

## Expected Files

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/041-executor-*.md`

## Test Plan

- Positive ready-state test for the synthetic fixture with exact golden mass,
  assembly-frame COM, and full inertia.
- Deterministic identity and order-invariance tests for reordered synthetic
  components, priors, and measurement entries.
- Regression tests proving the synthetic path rejects the checked-in real
  current-arm destinations.
- Regression tests proving the default real blocked path and default
  `--require-ready` behavior are unchanged.

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
- Proof that the synthetic path rejects either checked-in real destination.

## Reachability / Demo Proof

The executor must show both bounded paths:

- The real current-arm CLI remains blocked and unchanged.
- The synthetic fixture reaches `ready` through the same compiler logic or a
  tightly scoped test/demo entrypoint that cannot overwrite the tracked
  current-arm artifacts by accident.

## Cross-Doc Impact

- Supersedes brief 028 for the next executor turn.
- Keeps T16.4 open in `GOAL.md` and the task ledger.

## Out Of Scope

- The exact-cover overlap, parent/child overlap, reused-evidence, ambiguous
  mapping, and invalid transform/inertia negative matrix not strictly required
  to prove the first bounded synthetic happy path.
- Any real physical measurement intake.
- Any hardware census, actuation, calibration, or qualification work.
- Any M17+ experience-compiler, training, or optimizer work.
- Any unrelated cleanup in the already-dirty worktree.

## Stop Conditions

- Stop if the implementation would relabel CAD priors as measured evidence.
- Stop if the synthetic path can become the default current-arm input/output.
- Stop if validation requires hardware, external spend, or training.
