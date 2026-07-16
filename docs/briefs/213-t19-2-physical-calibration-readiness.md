# Slice Brief 213 - T19.2 Physical Calibration Readiness

**Date:** 2026-07-16

## Objective

Convert T19.2's broad calibration row into a source-bound, fail-closed readiness
contract before any torque change or motion. Bind the fresh T19.1 servo
snapshot, the signed calibration semantics, the last reviewed camera/session
state, the offline timing contract, and T16.6's pending motion requirements.
Emit one signed matrix that says exactly which prerequisites exist, which are
missing, and the smallest next physical-session implementation slice.

## Contract

- Recompute every positive fact from exact checked-in bytes and canonical
  project state. Do not trust caller booleans or aggregate readiness fields.
- Distinguish semantic calibration ranges from measured joint offsets; stable
  camera identity/mode from metric intrinsics/extrinsics; offline timing
  thresholds from live timing samples; raw gripper ticks from metric aperture;
  and owner access from a central motion permit.
- Require explicit evidence for a known metric calibration target, current
  camera roles and frames, camera intrinsics, camera-to-base extrinsics,
  held-out joint-offset samples, metric gripper aperture samples, live monotonic
  timing samples, and a tested watchdog/deadman/stop/exact-return harness.
- Mechanically keep `calibration_session_ready`, `motion_authority_ready`,
  `physical_twin_qualified`, and `physical_transfer_ready` false while any
  required evidence is missing.
- Route the next slice to an offline calibration-target and bounded
  micro-motion harness contract. No live gate is opened by this readiness
  report.

## Verification

Add tests for source substitution, stale/contradictory project state, forged
positive readiness, missing evidence, non-finite thresholds, nondeterministic
ordering, and authority escalation. Run exact artifact verification, relevant
calibration/timing/T19.1 tests, strict JSON, compilation, and diff checks.

## Authority withheld

This slice is offline. It grants no camera access, serial access, register
write, torque change, motion, calibration result, twin update, physical
qualification, transfer, policy actuation, external compute, or Brev use.
