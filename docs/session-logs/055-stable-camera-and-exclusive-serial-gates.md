# Session 055 - Stable Camera And Exclusive Serial Gates

**Date:** 2026-07-11

## Scope

Execute Brief 041 entirely offline after rejected attempt 001. Correct the
camera identity path, make finite frame evidence structurally verifiable, and
ensure any independent serial holder blocks before future hardware open.

## Implementation

- Replaced OpenCV numeric-index capture with an exact-name ffmpeg AVFoundation
  subprocess bound to the signed system unique ID/model.
- Made numeric index/order churn non-authoritative while retaining exact stable
  camera-name and system-identity sets.
- Added exact finite RGB24 PNG parsing with chunk bounds/CRC, zlib pixel data,
  scanline/filter, dimension, frame-count, timeout, exit, stderr, and trailing-
  byte checks.
- Added start/communicate/wait/read/release/terminate/kill/property-write and
  continuous-recording accounting through private and redacted evidence.
- Added normalized `lsof` holder parsing immediately before serial open and
  after no-write close. Any holder fails closed; the capture path never stops or
  signals it.
- Made canonical `live_gate: closed` a mandatory presence-lease condition.

## Verification

- Implementation commits: `ea99ec9`, `66003d8`, `fd13bf6`, `01802a0`.
- 19 dedicated tests, 35 combined census tests, and 214 broad tests passed.
- Both runtime offline verifiers passed with no enumeration or open.
- Black, `py_compile`, static no-write/no-aggregate/no-OpenCV checks, and
  `git diff --check` passed.

## Review

Reviewer decision 053 accepts the offline correction after remote preservation.
The complete diff remains unable to open hardware while canonical live state is
closed and will reject the currently observed Studio server before serial open
even if a later canonical decision reopens the lease gate.

## Authority state

- No hardware was enumerated or opened during Brief 041 implementation/testing.
- Rejected attempt 001 remains rejected with no bundle, manifest, or proof
  label.
- The pre-existing Studio server remains untouched; its last-observed holder
  status blocks exclusive bus ownership until a zero-holder check is authorized.
- No write, torque change, configuration, calibration, motion, policy
  actuation, physical qualification, or training occurred.
- `training_lock` remains closed.

## Next boundary

Commit/push the reviewer and canonical paths, confirm the named remote, then
request owner direction before stopping or releasing the pre-existing Studio
server. Continue offline if that authority is not granted.
