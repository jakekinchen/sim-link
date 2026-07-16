# Reviewer Decision 285 - Verify T19.2b Bounded Motion Harness

**Date:** 2026-07-16

## Decision

`ACCEPT FIXTURE-ONLY BOUNDED MOTION HARNESS; CONTINUE OFFLINE LIVE-AUTHORITY INTEGRATION`

Brief 215 implementation `17a20b5adbae009c4a0371ee2c2565475b6a06fe`
is on origin. Plan `739002d9...` binds the accepted T19.1 wrist-roll baseline
1320, servo ID 5, calibration range, +8 ticks / 0.7033 degrees, three-tick
tolerance, two settled samples, eight polls per leg, three-second watchdog,
deadman before every non-cleanup operation, voltage/temperature limits, exact
return, and one no-torque close.

Deterministic fixture result `1282784f...` performs 12 reads and the exact four
writes: torque enable, one target, exact baseline return, torque disable. It
records two torque transitions, two motion commands, one close, final torque
off, and exact return. `hardware_accessed=false` and
`physical_follower_commanded=false` remain explicit.

Fresh adversarial review checked source substitution, re-signed plan/result
drift, immutable-joint escape, forbidden registers, stale deadman, watchdog
expiry, wrong starting pose, pre-enabled torque, voltage/temperature bounds,
settling timeout, target overshoot, enable-write ambiguity, emergency-return
scope, torque-off cleanup, cleanup-error preservation, exactly-once close,
non-finite/malformed reads, and fixture-to-physical relabeling. The runner now
reverifies the exact source-bound plan and rejects non-fixture transports before
any operation. Fifty-three relevant tests pass in each pinned robotics runtime;
exact artifact verification, compilation, JSON, and diff checks pass.

This grants only `bounded_micro_motion_harness_fixture_conformant`. It grants no
live hardware constructor, physical motion, calibration result, twin update,
physical qualification, transfer, policy actuation, external compute, or Brev
authority. T19.2c must bind target-placement evidence, fresh runtime/state, a
central motion decision, and a one-use session permit before a live adapter can
even be proposed.
