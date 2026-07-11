# Slice Brief 031 - Fake-Bus Read-Only Census Harness

**Date:** 2026-07-10

## Objective

Start T16.5 with the smallest useful offline qualification-harness slice:
replay a recorded read-only servo census through a fake-bus/recorded-trace
contract so SceneSmith can prove the first identification path does not require
live hardware, register writes, or follower motion.

## Product / Project Value

T16.5 should not jump straight to broad fitting or qualification claims. The
next honest step is a bounded replay harness that turns one recorded census into
deterministic product evidence and makes write/motion safety testable offline.

## Acceptance Criteria

- Introduce one bounded recorded-trace or fake-bus contract for a read-only
  servo census relevant to the SO-101 twin foundation.
- The harness must replay the recorded census through production code rather
  than a test-only shadow path.
- The replay result must explicitly report that only read operations were used,
  with zero motor register writes and `physical_follower_commanded: false`.
- Add focused negative tests proving the harness fails closed if the trace
  contains a write operation, a forbidden follower port, or an unexpected
  register/shape mismatch.
- Keep the slice offline-only:
  no serial port open, no motion command, no claim of `physical_qualified`, and
  no mutation of the checked-in simulation-only qualification artifacts.

## Expected Files

- `scenesmith/robot_lab/leader_arm_bridge.py` or a new neighboring
  `scenesmith/robot_lab/` harness module
- `scripts/robot_lab/sample_leader_source.py` or a new bounded replay script
- `tests/unit/test_robot_lab_intervention.py` and/or a new focused robot-lab
  harness test module
- `tests/fixtures/robot_lab/` trace fixture(s) if needed
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `docs/session-logs/043-executor-*.md`

## Test Plan

- Positive unit test for replaying the recorded read-only census into the
  expected safety/result payload.
- Negative test for rejecting any write/register-mutation operation.
- Negative test for rejecting a forbidden follower port.
- Negative test for malformed or incomplete recorded trace content.
- Regression proof that the existing no-follower/read-only leader safety
  contract still holds.

## Validation Commands

- `python -m unittest tests.unit.test_robot_lab_intervention`
- `python -m py_compile scenesmith/robot_lab/leader_arm_bridge.py scripts/robot_lab/sample_leader_source.py`
- If a new module is added, include it in the same `py_compile` command.
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_robot_lab_intervention tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock`

## Evidence To Record

- The recorded-trace or fake-bus fixture identity/path used by the harness.
- The replay output fields showing read-only operation, zero register writes,
  and `physical_follower_commanded: false`.
- The exact failure messages for write-attempt, forbidden-port, and malformed
  trace rejection.
- Proof that no checked-in simulation-only qualification artifact changed.

## Reachability / Demo Proof

The executor must show the harness is reachable from a real repo-local product
path such as `scripts/robot_lab/sample_leader_source.py` or a new neighboring
CLI entrypoint, not only from direct unit calls.

## Cross-Doc Impact

- Brief 030 is closed by reviewer decision 038.
- This brief opens the first T16.5 slice only; it does not reopen T16.4.

## Out Of Scope

- Live hardware census, serial reads, calibration, or motion.
- Any claim of `physical_qualified` twin state.
- Broader T16.5 fitting/identification beyond the first read-only census path.
- Any M17+ compiler, training, or optimizer work.
- Any unrelated cleanup in the already-dirty worktree.

## Stop Conditions

- Stop if the implementation needs live hardware access or a real serial port.
- Stop if the slice would issue writes, motion, or follower commands.
- Stop if the slice would relabel offline replay evidence as physical
  qualification.
