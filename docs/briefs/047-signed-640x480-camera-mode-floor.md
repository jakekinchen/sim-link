# Slice Brief 047 - Signed 640x480 Camera Mode Floor

**Date:** 2026-07-11

## Objective

Prevent the deterministic selector from choosing the live-disproven sub-640
RealSense mode. Require every selected camera mode to be at least `640x480`,
then choose the smallest qualifying signed mode that supports integer 30 fps
within the reviewed 0.01-fps tolerance. Keep exact per-camera provenance and the
Brief 046 decoded-dimension enforcement. Keep `live_gate` closed.

## Evidence basis

- Attempt 005 requested `424x240` for RealSense but observed `640x480`.
- The signed discovery-v2 artifact contains qualifying `640x480` modes at
  30.000030 fps for both the C922 and RealSense cameras.
- A 640x480 floor is also a more useful minimum for later policy preprocessing;
  it remains finite and is selected only from each camera's own signed modes.

## Contract

- Add explicit reviewed minimum width and height constants of 640 and 480.
- Filter signed supported modes by the minimum dimensions and 30-fps tolerance
  before deterministic area/pixel-format ordering.
- Fail closed if any selected camera lacks a qualifying mode. Do not fall back
  to a default or copy another camera's mode.
- Bind the selected dimensions through contract, command, audit, diagnostics,
  private evidence, manifest, and exact decoded-output verification.

## Validation and authority

Test sub-floor rejection, exact-floor acceptance, per-camera independence,
30.000030 tolerance, no qualifying mode, and attempt-005 selection regression.
Run focused and broad offline gates, both runtimes, legacy evidence, compile,
privacy, and diff checks. No hardware discovery/open, Studio request, reconnect,
write, torque change, motion, policy actuation, optimizer, paid compute, or
destructive action. `training_lock` and `live_gate` remain closed.
