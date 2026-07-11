# Slice Brief 032 - Unify Executable Robotics Stack

**Date:** 2026-07-10

## Objective

Complete T16.1b by replacing the accepted `split_runtime_unresolved` state with
one reproducible LeRobot executable identity used by collection, training,
checkpoint finalization, and inference.

## Acceptance Criteria

- Pin one exact 40-character LeRobot base commit.
- Preserve SceneSmith PI0.5/training changes as a deterministic tracked patch-set
  with content identity; no required behavior may live only in an uncommitted
  nested checkout or an undocumented host environment variable.
- Provide one resolver/validator that every robotics stage can call before it
  imports LeRobot or consumes a LeRobot-produced artifact.
- Record the complete executable identity in the robotics dependency lock,
  including base revision, ordered patch hashes, relevant source tree hash,
  dependency/environment lock hash, and critical non-secret configuration.
- Reject LeLab's divergent `v0.6.0` runtime resolution rather than recording it
  as an expected valid split.
- Add a saved-sample conformance test that proves collection-time,
  training-time, and inference-time processors produce the same tensors and
  compatible round-trip actions under the unified identity.
- Keep `training_lock: closed`; do not run an optimizer.

## Expected Files

- `scenesmith/robot_lab/robotics_dependency_lock.py`
- a shared executable-stack/processor contract under `scenesmith/robot_lab/`
- `scripts/robot_lab/patches/`
- collection, training, finalization, and inference entrypoints as needed
- focused tests and checked-in lock/config artifacts
- workflow state, executor log, and reviewer decision

## Validation

- Focused dependency-lock and executable-stack unit tests.
- Patch dry-run/application verification from the pinned clean base.
- Saved-sample collection/training/inference conformance test.
- Product entrypoint checks proving each stage rejects a missing or mismatched
  executable identity before importing or consuming LeRobot artifacts.
- Broad robot-lab regression gate.

## Out Of Scope

- Any optimizer run, hardware access, measured-inertial change, qualification
  status change, T16.5 work, or unrelated dirty-worktree cleanup.

## Stop Conditions

- Stop if the only way to pass is to treat an uncommitted nested checkout as a
  durable executable revision.
- Stop if collection, training, finalization, or inference can silently fall
  back to a different installed LeRobot package.
