# Slice Brief 048 - Signed Calibration Profile

**Date:** 2026-07-11

## Objective

Parse the pinned follower calibration JSON into a signed, tracked
`CalibrationProfile` bound to accepted T16.5b manifest `eff3c824...` and its six
live servo identities. This is the first offline T16.5c prerequisite.

## Contract

- Require exactly the six accepted joint names and servo IDs with no duplicate.
- Require integer finite homing offsets, `range_min < range_max`, reviewed raw
  bounds, and expected drive mode zero.
- Bind the source path by hash/size, accepted manifest identity, servo identity
  digest, and explicit units/normalization semantics.
- Body joints use raw-position-to-degree calibration semantics; gripper uses an
  explicit range normalization with declared open/closed endpoint meaning.
- Reject missing/extra joints, ID/name mismatch, duplicate ID, booleans,
  non-finite/non-integer values, inverted/out-of-domain ranges, unexpected drive
  mode, source/manifest substitution, and resigned semantic drift.

## Evidence and authority

Write a redacted tracked profile under `configurations/robot_lab/` and retain no
raw device path or serial. Add deterministic tests and an offline verifier.
No hardware access, policy preprocessing/inference, MuJoCo replay, write, torque
change, motion, physical qualification, optimizer, or paid compute.
`training_lock` and `live_gate` remain closed.
