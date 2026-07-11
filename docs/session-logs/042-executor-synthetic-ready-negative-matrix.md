# Executor Session 042 - Synthetic Ready Negative Matrix

**Date:** 2026-07-10

## Slice

Land the smallest useful follow-up to the synthetic happy-path proof: keep the
bounded `synthetic_test_only` compiler behavior unchanged on the real current-arm
path, but add durable negative-matrix proof for exact-cover ambiguity, reused
evidence, and malformed transform/inertia inputs. One narrow code change was
required so a one-measurement synthetic intake reaches the exact-cover compiler
gate instead of failing earlier in fixture-shape validation.

## Files Changed

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

Unrelated dirty-worktree changes were present at start and were left untouched.

## Tests / Validation

- `python -m unittest tests.unit.test_measured_inertial_intake`
- `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
- `python scripts/robot_lab/write_measured_inertial_intake.py --intake tests/fixtures/robot_lab/measured_mass/synthetic_complete.json --output /private/tmp/scenesmith-next-synthetic-ready.json --require-ready`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

## Reachability

Real product path remained blocked through the shipped CLI:

- `python scripts/robot_lab/write_measured_inertial_intake.py --verify` still
  verified the checked-in real artifacts.
- `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
  still exited nonzero because the real output remains `blocked_missing_measurements`.

Bounded synthetic reachability also remained live through the same product path:

- `python scripts/robot_lab/write_measured_inertial_intake.py --intake tests/fixtures/robot_lab/measured_mass/synthetic_complete.json --output /private/tmp/scenesmith-next-synthetic-ready.json --require-ready`
  still produced a `ready` artifact only when the caller supplied both the
  explicit synthetic fixture and a non-real output destination.

All new negative cases call `build_assembly_inertials(...)` on variant synthetic
fixture payloads, so they exercise the same measured-intake verification and
assembly compiler path used by the CLI rather than a shadow implementation.

## Evidence

- Happy-path synthetic ready identity remained
  `9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d`.
- Happy-path synthetic aggregate mass/COM/inertia remained:
  `4.5` kg,
  `[0.35, 0.283333333, 0.033333333]`,
  `[[0.073625, -0.053025, 0.26218125], [-0.053025, 1.1719375, 0.0126125], [0.26218125, 0.0126125, 1.11475]]`.
- Default blocked real identities remained:
  intake `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
  and output `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`.
- New negative failure reasons now pinned by tests:
  `Synthetic measurements did not form an exact cover of required atoms`
  `Synthetic coverage atom was selected more than once: alpha_structure_mass`
  `Synthetic measurements must cover exactly one atom`
  `Synthetic measurement evidence was reused: synthetic_beta_measurement`
  `synthetic_alpha_cad_prior rotation must be orthonormal`
  `synthetic_alpha_cad_prior source inertia must be symmetric`

## Step-9 Flags For Reviewer

- Verify that relaxing the synthetic measurement-count precheck from `>= 2` to
  `>= 1` is the intended boundary: zero-measurement fixtures still fail early,
  while incomplete nonempty fixtures now fail at the exact-cover compiler gate.
- Confirm brief 030 is satisfied without widening the synthetic path into any
  default current-arm input/output route.
- Confirm no checked-in real artifacts changed and no unrelated dirty files were
  included in the slice.

## Next Suggested Slice

If brief 030 is accepted, close T16.4 in review and start the smallest T16.5
fake-bus/recorded-trace qualification-harness slice.
