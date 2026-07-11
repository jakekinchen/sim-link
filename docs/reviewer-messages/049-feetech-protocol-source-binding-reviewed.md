# Reviewer Decision 049 - Feetech Protocol Source Binding Reviewed

**Date:** 2026-07-11

## Decision

`CLOSE CORRECTED T16.5a AFTER REMOTE PRESERVATION; KEEP T16.5b CLOSED UNTIL THEN`

## Review target

Correction commits `51024221a3175bddedb0eabbfdf4de3b862c3862` and
`eeb16e1c1ad93eec26f972177d758e6a6d1a3b7e` under Brief 040.

## Findings

- The v2 fixture contract now declares Feetech protocol `0`, matching both the
  pinned constructor default and `MODEL_PROTOCOL["sts3215"]`.
- Four exact source hashes bind the Feetech implementation/table, generic bus
  lifecycle, and SOFollower joint map used by the census.
- A separate AST verifier independently derives protocol defaults, model
  protocol, baud/default code, model number 777, resolution 4096, all eight
  register widths, connect/disconnect defaults and guards, and the exact six-
  joint IDs/models.
- The verifier proves `_handshake()` is guarded by `handshake`, `openPort()` is
  outside that guard, torque disable is guarded by `disable_torque`, and
  `closePort()` is outside the torque-write guard. Thus the reviewed adapter's
  explicit false arguments both avoid writes and still open/close the port.
- Census joint, model, resolution, protocol, baud, and register constants are
  derived from the verified semantic table rather than separately duplicated.
- Artifact writing and checked-in verification both fail on source hash or
  semantic drift. A test that tampers with protocol and updates the expected
  hash still fails the semantic verifier.
- Protocol `1` is retained only as a negative mutation and cannot satisfy the
  v2 contract or reach a live constructor.
- The trace/result remain fixture-only, with no hardware opened, no follower
  command, and zero writes, torque changes, or motion commands.

## Evidence

- 16 focused census/source-binding tests passed.
- 195 feeding/consuming tests passed in 70.709 seconds.
- Corrected v2 contract identity:
  `73652ffa885f159da0412e4e151203805b5d9ce12138e137d4fd951f82276978`.
- Corrected recorded trace identity:
  `17921a5f7a406aba6b05efca56697a692969fc16f268c863260f2c6274b542d1`.
- Corrected fixture result identity:
  `4a83298bb0c6cb4d4416e99e7976598de3455644a6841d1550f0362109804986`.
- Offline census, authority, qualification, twin, structural-twin, dependency-
  lock, and LeRobot product verifiers exited zero; every global decision stayed
  withheld.
- Black, `py_compile`, static no-live-factory/no-write inspection, and
  `git diff --check` passed.

## Review-time corrections

Review bumped the changed contract shape to v2, derived every census constant
from verified semantics, and added structural proof that port open/close calls
remain outside the handshake and torque-write guards. Final artifacts and every
test/product gate were rerun afterward.

## Authority

After remote preservation, this restores only `census_trace_conformant` for the
corrected offline fixture and permits re-entry to T16.5b under its separate
owner-presence lease. It grants no serial/camera open by itself, live observation
claim, write, torque change, motion, physical qualification, training, transfer,
promotion, or global decision. Hardware was not accessed and `training_lock`
remains closed.
