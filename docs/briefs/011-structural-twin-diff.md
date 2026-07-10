# Slice Brief 011 - Structural Twin Diff

**Date:** 2026-07-10

## Objective

Complete T16.3 by generating a deterministic, machine-readable structural diff
between the active Robot Studio SO-101 runtime model and the pinned Menagerie
`robotstudio_so101` lineage, while preserving the current runtime inputs.

## Product / Project Value

M16 cannot claim a truthful twin foundation if the repo silently treats the
active Robot Studio model as equivalent to Menagerie. This slice must make the
structural gap explicit so later inertial intake, qualification, and compiler
work bind to a named baseline rather than an assumed match.

## Acceptance Criteria

- A checked-in artifact records the structural diff between the active runtime
  files pinned in `configurations/robot_lab/pi05_robotics_dependency_lock.json`
  and the pinned Menagerie `robotstudio_so101` source files.
- The diff is deterministic and content-addressed or otherwise hash-bound to the
  exact source files it compares.
- The artifact reports at least the categories named by T16.3:
  inertials, joint limits, contacts, cameras, gripper, actuators, and
  backlash/friction placeholders or explicit unknowns when they are not encoded
  in one source.
- The output distinguishes matched, mismatched, missing, and extra structural
  elements rather than collapsing everything into free-form text.
- A real CLI writes and verifies the artifact from repo state.
- Focused tests cover deterministic generation and drift/tamper failures.
- Broader robot-lab validation still passes.

## Expected Files

- `scenesmith/robot_lab/structural_twin_diff.py` or an equivalently named
  robot-lab module for parsing and comparing the pinned model sources.
- `scripts/robot_lab/write_structural_twin_diff.py` or an equivalently named CLI.
- `tests/unit/test_structural_twin_diff.py`
- One checked-in structural diff artifact under `configurations/robot_lab/`
- `docs/session-logs/NNN-executor-*.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`

## Test Plan

- Add focused unit coverage for deterministic diff generation.
- Add negative tests for source-hash drift, stale/tampered artifact identity,
  and category omissions.
- If parser behavior depends on XML normalization, prove equivalent source
  formatting yields identical structural output.

## Validation Commands

- `python -m unittest tests.unit.test_structural_twin_diff`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Evidence To Record

- The artifact path and identity/hash.
- The exact runtime and Menagerie source paths and hashes compared.
- A concise category summary of the mismatches and explicit unknowns discovered.
- Focused and broad validation results.
- Reachability showing the diff is generated directly from the pinned dependency
  lock inputs, not hard-coded duplicate paths.

## Reachability / Demo Proof

The slice is only done if the CLI resolves the runtime and Menagerie sources
from the tracked dependency lock and emits/verifies the checked-in artifact from
repo state. T16.4 and later M16-M19 work must be able to consume this artifact
as the declared structural baseline.

## Cross-Doc Impact

- Update `GOAL.md` and `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
  only after the diff artifact is verified.
- If this slice exposes a stale twin-contract assumption or new required
  requalification trigger, route that correction through the ledger and session
  log rather than burying it in code comments.

## Out Of Scope

- Switching the active MJCF or URDF runtime inputs.
- Physical bus reads, motion, contact, or any M19 qualification claim.
- T16.4 measured-mass intake and inertia compilation.
- Any scene-generation, asset-pipeline, or prompt changes already present in the
  dirty worktree outside robot-lab scope.
- Training, evaluation, or replay changes.

## Stop Conditions

- Stop if the comparison requires changing the pinned runtime inputs rather than
  describing them.
- Stop if the source files named by the dependency lock cannot be read or do not
  match the recorded lock identities.
- Stop if the slice drifts into physical qualification semantics instead of
  structural reconciliation.
