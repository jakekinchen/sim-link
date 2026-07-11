# Reviewer Decision 047 - Offline No-Write Servo Census Reviewed

**Date:** 2026-07-11

## Decision

`CLOSE T16.5a AFTER REMOTE PRESERVATION; CONTINUE T16.5b ONLY UNDER AN ACTIVE OWNER-PRESENCE LEASE`

## Review target

Implementation commit `f2000870775c175f1331bf42c0521d7067462a92`
under Brief 038.

## Findings

- The census receives only an injected protocol exposing device identity,
  connection state, connect, one-register read, no-write close, and audit. It
  cannot call a write, torque, configuration, calibration, scan, or action
  method through that protocol.
- The code-pinned fixture contract binds the follower role, complete USB and
  bus identity, rejected leader aliases, IDs 1-6, exact joint mapping, STS3215
  model number 777, eight-register read allowlist, and one-retry maximum.
- The joint map, model number, register widths, and read-only register semantics
  match the pinned LeRobot source. The adapter calls only
  `connect(handshake=False)`, scalar `read(..., normalize=False, num_retry=0)`,
  and `disconnect(disable_torque=False)`.
- A connect attempt is treated conservatively as potentially open even if it
  raises. Cleanup then calls the explicit no-write disconnect exactly once and
  preserves both a primary failure and any cleanup failure in one exception
  group.
- Positive traces must contain exactly one construct, one connect, all 48 reads
  in canonical servo/register/retry order, and one successful no-write close.
  Missing, extra, duplicate, malformed, out-of-order, non-allowlisted, or
  write-like operations fail closed.
- Device role, VID, PID, serial, canonical path, aliases, protocol, baud, model,
  servo ID, register width/type, position range, and temperature range are
  mechanically checked. Only declared transient read failures are retryable.
- The signed fixture result is labeled only `census_trace_conformant`, remains
  `qualification_scope=fixture_evidence`, and records
  `hardware_opened=false`, `physical_follower_commanded=false`, 49 read
  attempts, 48 successes, one retry, and zero writes, torque changes, motion
  commands, or unexpected operations.
- The offline module and CLI contain no LeRobot, serial, or camera import or
  live-factory call. The existing physical-leader bridge teardown now also
  passes `disable_torque=False`, closing an unsafe default without opening any
  hardware during this slice.

## Evidence

- 14 focused census tests passed.
- 193 feeding/consuming tests passed in 70.985 seconds, including intervention
  leader safety, computed qualification, numerical/artifact contracts, central
  authority composition, production/blocked inertials, twin, structural twin,
  dependency lock, and LeRobot stack tests.
- Contract identity:
  `17e8c712d88877fd508266fa85cd34bd14da8fbdd7bc98ac5ff7955bd708c2a0`.
- Recorded trace identity:
  `25cbac27c7e86aed9ae14cf691f14f4293c14b8c85db9ee500e993650c59e27c`.
- Fixture result identity:
  `e7c0ecfc53328571fa4e695fcb53d50b54acaa24a1d34cbe8c45eb709efbc394`.
- The offline census, computed qualification, default authority, legacy twin,
  structural-twin, dependency-lock, and LeRobot product verifiers all exited
  zero. Every central global decision remained withheld.
- `py_compile`, Black formatting for the three new Python files, static
  no-live-factory inspection, and `git diff --check` passed.

## Review-time corrections

Review added complete positive read-sequence validation, malformed and
missing/extra event rejection, duplicate servo-ID rejection, content-identity
ordering and mutation tests, full USB/bus/alias negative coverage, conservative
partial-connect cleanup, a robust import guard, and BaseException-safe dual-error
preservation. All focused, broad, product, compile, and diff gates were rerun
after those corrections.

## Authority

After remote preservation, this establishes only `census_trace_conformant` for
the declared offline fixture and permits entry to T16.5b while the
owner-presence lease is active. It does not itself authorize a serial/camera
open, live observation claim, register write, torque change, motion, physical
qualification, global readiness decision, optimizer run, or training. Hardware
was not accessed and `training_lock` remains closed.
