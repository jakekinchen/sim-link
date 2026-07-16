# Slice Brief 215 - T19.2b Bounded Micro-Motion Harness

**Date:** 2026-07-16

## Objective

Implement and fixture-test the missing watchdog/deadman/stop/exact-return
motion harness without exposing a live hardware constructor. Bind one
sub-degree wrist-roll delta to the fresh T19.1 pose and signed calibration
ranges. This is an offline capability slice, not a motion permit.

## Motion template

- Selected joint: wrist roll, servo ID 5; all other joints and the gripper are
  immutable.
- T19.1 baseline: raw position 1320. Fixture delta: +8 ticks (approximately
  0.703 degrees), then exact return to 1320.
- Preflight requires torque disabled, exact current pose within three ticks,
  11.0-13.0 V, temperature no higher than 45 C, a fresh deadman token, and
  an unexpired three-second watchdog.
- Only `Torque_Enable` and `Goal_Position` writes may occur. The success path is
  torque enable, one bounded target, two consecutive settled samples, exact
  return, two consecutive settled samples, torque disable, final torque-off and
  return verification, then `disconnect(disable_torque=False)`.
- Every write and poll requires the deadman. Any failure routes through a
  bounded best-effort return-to-baseline and torque-off cleanup before no-write
  close. Failure cleanup never widens the joint, delta, register, or time scope.

## Verification

Use only an injected fake/recorded transport. Test success, stale/dead deadman,
watchdog expiry, wrong starting pose, torque already enabled, voltage/
temperature rejection, forbidden register/joint, target overshoot, settling
timeout, failure cleanup, cleanup failure preservation, trace tampering,
non-finite data, and re-signed authority escalation. Run relevant T19.1,
calibration, authority, compilation, JSON, and diff gates.

## Authority withheld

No serial/camera enumeration or open, live bus construction, register write,
torque change, motion, calibration update, physical qualification, transfer,
policy actuation, external compute, or Brev use is granted. A future live path
still needs target placement proof, current runtime/profile, central motion
decision, exact session permit, owner presence, fresh pose/telemetry, and a
separate reviewed remote gate.
