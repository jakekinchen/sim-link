# Session 052 - Live Read-Only Observation Harness

**Date:** 2026-07-11

## Scope

Implement and review the offline gate for T16.5b before any operating-system
metadata discovery, serial open, camera open, or other live-object use.

## Implementation

- Added separate `verify-offline`, `discover`, `prepare`, and `capture` command
  surfaces so offline proof cannot accidentally enumerate or open hardware.
- Added short signed owner-presence leases and signed live execution contracts
  bound to corrected T16.5a source semantics, exact discovered identities, the
  pinned follower calibration file, selected cameras, and the hard closeout.
- Added a raw-bus adapter exposing only no-handshake connect, allowlisted scalar
  reads, and no-torque disconnect with one bounded outer retry and paired cleanup
  error preservation.
- Added finite camera capture with host wall/monotonic timestamps, content
  hashes, read watchdog, and release cleanup.
- Added immutable private raw evidence plus a separate signed, content-addressed,
  privacy-redacted tracked manifest.

## Verification

- Implementation commit: `16d24ea0c4ced2b62d3ba2c0297f1816981efee3`.
- 14 dedicated live-harness tests passed.
- 30 combined live-harness/census tests passed.
- 209 broad regression tests passed in 71.561 seconds.
- Offline verification passed under both `.mujoco_venv` and
  `external/leLab/.venv`, with corrected protocol 0 and all four pinned source
  hashes.
- Black, `py_compile`, static no-write/no-aggregate inspection, and
  `git diff --check` passed.

## Review

Reviewer decision 050 accepts the offline harness and permits only metadata
discovery after the implementation/review boundary is remotely preserved. Brief
039's stale pre-correction T16.5a ancestry was corrected during review.

## Hardware and authority state

- No USB/serial/camera metadata was enumerated in this slice.
- No live bus, follower, serial port, or camera was constructed or opened.
- No register write, torque change, configuration, calibration, motion, policy
  actuation, or optimizer training occurred.
- No live proof label is granted. `training_lock` remains closed.

## Next boundary

Commit and push only the reviewer/canonical paths, confirm the exact named
remote, then perform one metadata-only discovery. Any ambiguous follower,
leader collision, missing identity, camera mismatch, or remote drift fails
closed before device open.
