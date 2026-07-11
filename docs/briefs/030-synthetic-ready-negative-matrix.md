# Slice Brief 030 - Synthetic Ready Negative Matrix

**Date:** 2026-07-10

## Objective

Implement the next smallest useful T16.4 slice after the synthetic happy-path
proof: keep the bounded `synthetic_test_only` ready compiler working, but add
the remaining fail-closed negative matrix for exact-cover ambiguity,
reused-evidence, and invalid transform/inertia input.

## Product / Project Value

T16.4 is not complete just because the synthetic path can compile one golden
fixture. The compiler also needs to prove it rejects ambiguous or malformed
synthetic measured evidence without weakening the blocked real-arm path.

## Acceptance Criteria

- Preserve the current happy-path proof for
  `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`, including
  the ready identity
  `9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d`,
  golden mass `4.5` kg, COM `[0.35, 0.283333333, 0.033333333]`, and golden
  inertia
  `[[0.073625, -0.053025, 0.26218125], [-0.053025, 1.1719375, 0.0126125], [0.26218125, 0.0126125, 1.11475]]`.
- Add focused negative tests proving the bounded synthetic path fails closed for
  exact-cover ambiguity:
  missing required atom coverage, duplicate active coverage of one required
  atom, or any other ambiguous selected-measurement set that prevents one exact
  cover of required atoms.
- Add focused negative tests proving synthetic evidence cannot be reused across
  active measurements.
- Add focused negative tests proving malformed transform or inertia inputs fail
  closed on the synthetic path. Include at least one invalid rotation case and
  one invalid inertia-matrix case.
- Keep the synthetic path bounded:
  it must still refuse either checked-in real current-arm destination and must
  not become the default current-arm input/output path.
- Keep default real-path write/verify semantics unchanged, and default
  `--require-ready` must still exit nonzero against the blocked real artifact.

## Expected Files

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/042-executor-*.md`

## Test Plan

- Positive regression test for the existing synthetic ready fixture so the happy
  path stays pinned while negative cases are added.
- Negative exact-cover tests for missing required coverage and duplicate active
  coverage of one required atom.
- Negative reused-evidence test for active evidence reuse across measurements.
- Negative malformed-transform test and malformed-inertia test on synthetic
  measured compilation.
- Regression tests proving the synthetic path still refuses the checked-in real
  current-arm destinations.
- Regression tests proving the default real blocked path and default
  `--require-ready` behavior are unchanged.

## Validation Commands

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- `python scripts/robot_lab/write_measured_inertial_intake.py --intake tests/fixtures/robot_lab/measured_mass/synthetic_complete.json --output /private/tmp/scenesmith-next-synthetic-ready.json --require-ready`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

## Evidence To Record

- The preserved happy-path ready identity and golden aggregate values for the
  synthetic fixture.
- Negative-test names and exact failure reasons for exact-cover ambiguity,
  reused evidence, invalid rotation, and invalid inertia rejection.
- Proof that the default blocked real identities remain:
  intake `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
  and output `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`.
- Proof that the synthetic path still refuses either checked-in real
  destination.

## Reachability / Demo Proof

The executor must show both bounded paths again:

- the real current-arm CLI remains blocked and unchanged;
- the synthetic fixture still reaches `ready` only through an explicit
  synthetic fixture input plus a non-real output destination;
- the new negative cases fail through the same compiler path rather than a
  test-only shadow implementation.

## Cross-Doc Impact

- Supersedes brief 029 for the next executor turn.
- Keeps T16.4 open in `GOAL.md` and the task ledger until the negative matrix is
  accepted in review.

## Out Of Scope

- Any real physical measurement intake.
- Any hardware census, actuation, calibration, or qualification work.
- T16.5 fake-bus or qualification harness work.
- Any M17+ experience-compiler, training, or optimizer work.
- Any unrelated cleanup in the already-dirty worktree.

## Stop Conditions

- Stop if the implementation would relabel CAD priors as measured evidence.
- Stop if the synthetic path can become the default current-arm input/output.
- Stop if the negative-matrix proof requires hardware, external spend, or
  training.
