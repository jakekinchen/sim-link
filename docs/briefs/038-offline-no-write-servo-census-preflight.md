# Slice Brief 038 - Offline No-Write Servo Census Preflight

**Date:** 2026-07-11

## Objective

Complete T16.5a entirely offline. Build and verify the production census logic
against injected fake/recorded transports before any serial, camera, leader,
follower, or servo-bus object is opened. Prove construction, connect, reads,
decode, bounded retry, exception cleanup, and close can execute with zero motor
register writes, zero torque changes, zero motion commands, and
`physical_follower_commanded=false`.

## Safety context

The generic LeRobot bus exposes writes and defaults `disconnect()` to torque
disable, which itself writes motor registers. `SOFollower.connect()` also
configures motors and cameras. Neither broad object is a valid T16.5a or T16.5b
surface. Census code receives only a narrow read-only protocol, and any future
adapter must close with `disconnect(disable_torque=False)` or an equivalently
proven raw-port close. Teardown must never torque-disable, configure, calibrate,
or write.

## Required contracts

- Define a narrow injected transport with only bounded connect, single-servo
  read, connection-state, and no-write close operations. The census function
  must not receive or recover a writable bus object.
- Record an exact expected device role, canonical USB identity fields (VID,
  PID, serial, protocol, baud), rejected aliases, and the six SO-101 joints:
  IDs 1-6, model `sts3215`, with gripper at ID 6.
- Use an explicit read allowlist for identity and telemetry. Any write-like,
  configuration, goal, torque, calibration, setup, scan, or unknown register
  operation fails before transport execution.
- Model lifecycle states and operation counts explicitly: construct, connect
  attempts/successes, read attempts/successes, retries, close calls, register
  writes, torque changes, motion commands, and unexpected operations.
- Retry only declared transient read failures, with a fixed deterministic bound.
  Identity mismatch, malformed data, write attempts, and forbidden operations
  are not retryable.
- Exception cleanup must close exactly once through the no-write close path.
  Close failure remains visible and cannot be hidden by an earlier exception.
- Emit a signed/content-addressed recorded-trace result labeled only
  `census_trace_conformant`, with `hardware_opened=false`,
  `physical_follower_commanded=false`, and every write/torque/motion count zero.

## Adversarial acceptance

- Reject wrong role, VID/PID/serial/protocol/baud, port-only identity, known
  leader/follower alias ambiguity, duplicate/missing/unexpected servo IDs,
  wrong model/joint mapping, and duplicate identity records.
- Reject write, sync-write, torque enable/disable, calibration, configuration,
  setup, goal-position, motion, scan, and teardown-write attempts even when a
  trace is resigned.
- Reject unknown registers, wrong widths/types/shapes, non-finite decoded
  values, missing reads, extra reads, out-of-order lifecycle events, reads while
  disconnected, double close, retry exhaustion, and cleanup that masks errors.
- Prove result identity is invariant to irrelevant input dictionary ordering but
  changes with any operation/value/evidence change.
- Add a static/source guard showing the offline CLI cannot import-construct or
  call live LeRobot/camera/serial factories.

## Validation

- Focused recorded-transport/lifecycle suite, including success, transient
  retry, decode, write-attempt, identity, malformed-shape, exception-cleanup,
  close-failure, and static no-live-construction tests.
- Existing intervention leader safety, computed qualification, authority,
  twin, structural-twin, dependency-lock, and LeRobot regression gate.
- Product CLI verifies the checked-in trace/result deterministically without
  enumerating or opening devices.
- `py_compile` and `git diff --check`.

## Out of scope

Port enumeration, USB discovery, serial open, live reads, camera access,
calibration, torque state changes, writes, motion, observation capture, policy
shadow, MuJoCo matching, physical qualification, optimizer work, and paid
compute.

## Authority after this slice

If reviewed and remotely preserved, this may establish only
`census_trace_conformant` for the declared offline fixture and authorize entry
to the separately gated T16.5b live read-only task while the owner-presence
lease is active. It grants no physical observation fact, no register write, no
motion, no physical qualification, and no global authority decision.
