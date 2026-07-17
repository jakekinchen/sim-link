# Slice Brief 228 - Owner-Present RGB-Only Camera Census

**Date:** 2026-07-16

## Objective

Run one bounded, owner-present camera-only census for the Intel RealSense D405
UVC RGB device (VendorID 32902 / ProductID 2907) and Logitech C922 Pro Stream.
Record each camera's signed AVFoundation stream modes, open exactly one RGB
stream at a reviewed 30 fps mode, retain exactly one signed PNG frame, and
measure coarse host receive latency with T20.22 timing vocabulary.

## Authority and entry gates

- The current owner-present authorization is camera-only and finite. Before
  camera metadata enumeration or open, the exact current Codex thread must pass
  the formal `danger-full-access` plus approval-policy `never` verifier.
- A central decision and content-addressed one-use permit must bind the exact
  branch/origin boundary, Brief 228 state, runtime identity, two target camera
  selectors, one frame per camera, RGB-only operation, ten-minute capture
  ceiling, private destination, and tracked redacted manifest destination.
- Implementation, deterministic tests, same-agent review, the open-gate state,
  commit, and remote preservation must agree before preflight may grant.

## Exact live sequence

1. Reverify runtime, central decision, permit, branch/origin boundary, owner
   window, output absence, and source bindings without enumerating hardware.
2. Enumerate camera metadata only through `system_profiler`, AVFoundation, and
   signed AVFoundation format inspection. Do not enumerate or open serial.
3. Resolve exactly one D405 by its required vendor/product IDs and exactly one
   C922 by name; reject missing or ambiguous identity.
4. Preserve all achievable signed RGB stream configurations. Select the
   smallest advertised mode of at least 640x480 that supports exact 30 fps.
5. Open each exact named AVFoundation RGB source sequentially, capture exactly
   one PNG, close it, and retain signed frame hash/dimensions/timestamps plus a
   coarse host receive interval. Total capture duration must not exceed 600 s.
6. Emit immutable private frames/evidence and a tracked redacted manifest, then
   close and consume the gate on success or failure.

Depth, librealsense, serial access, robot construction, writes, configuration,
motion, torque, policy/model/optimizer action, network acquisition, external
compute, and Brev are prohibited.

## Acceptance and proof boundary

- Tests must cover authority denial, stale/forged boundaries, path escape,
  device absence/ambiguity, unsupported mode, duplicate/excess frames,
  timestamp regression, unsafe camera audits, evidence tampering, and private
  identity redaction.
- A successful result grants only
  `owner_present_rgb_camera_census_observed`. It is hardware-readiness evidence,
  not calibration, synchronized timing, frame-age proof, depth capability,
  physical-twin qualification, transfer readiness, or policy success.
