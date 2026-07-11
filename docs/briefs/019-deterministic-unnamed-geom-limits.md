# Slice Brief 019 - Deterministic Unnamed Geom Limits

**Date:** 2026-07-10

## Objective

Close the last open T16.3 semantic gap by making unnamed-geom comparison output
deterministic and reviewable without reopening quaternion, inertial/contact, or
measured-mass work.

## Product / Project Value

T16.3 cannot close while structural-diff records still depend on unstable
unnamed collision identifiers. This slice finishes the deterministic evidence
contract needed before T16.4 measured-mass intake can reopen.

## Acceptance Criteria

- Remaining unnamed-geom records in the structural twin diff use deterministic
  identifiers or deterministic grouping that is stable across repeated artifact
  generation.
- Focused regressions prove the intended behavior for at least one repeated
  unnamed-geom scenario that previously produced unstable or ambiguous output.
- Re-running `scripts/robot_lab/write_structural_twin_diff.py` preserves the
  checked-in artifact identity after the first write.
- Existing quaternion, inertial `unknown`, and friction/contact truthfulness
  regressions stay green.
- The artifact preserves explicit `adopt`, `adapt`, or `retain` decisions for
  any remaining mismatch, missing record, extra record, or surfaced unknown.

## Expected Files

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/NNN-executor-*.md`

## Test Plan

- Add focused regression coverage for deterministic unnamed-geom handling.
- Prove repeat generation stability for the affected structural-diff output.
- Keep the existing quaternion and inertial/contact truthfulness regressions
  passing.

## Validation Commands

- `python -m unittest tests.unit.test_structural_twin_diff`
- `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Evidence To Record

- One scoped commit for this slice only.
- Updated structural-diff artifact identity.
- Executor log that states exactly which unnamed-geom cases became
  deterministic and whether any deterministic limits still remain in T16.3.

## Reachability / Demo Proof

Prove the behavior through `scripts/robot_lab/write_structural_twin_diff.py`
with a sequential write then `--verify` run against the checked-in artifact.

## Cross-Doc Impact

- Update the T16.3 ledger entry and milestone log with the new artifact
  identity, validation counts, and whether T16.3 can now close or still carries
  a deterministic identifier residue.
- Update `GOAL.md` only if the T16.3 next step changes after this slice lands.

## Out Of Scope

- Quaternion normalization or transform semantics.
- Inertial `unknown` handling or friction/contact attachment truthfulness.
- T16.4 measured-part mass intake and inertia/COM compilation.
- Hardware access, authority-gated work, or Brev usage.
- Any T17+ compiler or training activity.

## Stop Conditions

- Stop if deterministic unnamed-geom repair would require silent structural
  relabeling that hides a real Menagerie-vs-runtime semantic delta.
- Stop if the only available fix would reopen already accepted quaternion or
  inertial/contact behavior instead of isolating identifier determinism.
