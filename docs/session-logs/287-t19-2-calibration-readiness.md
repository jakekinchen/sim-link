# Session 287 - T19.2 Calibration Readiness

**Date:** 2026-07-16

After T19.1 was remotely verified, Brief 213 audited the actual calibration
surfaces instead of treating broad owner hardware authorization as a motion
permit. Report `5476d01d...` binds the fresh servo snapshot, calibration
semantics, historical camera review, offline timing fixture, and pending T16.6
state.

The exact missing set is: central motion authority, a current metric target,
camera intrinsics, camera-to-base extrinsics, held-out joint-offset motion
samples, metric gripper-aperture samples, live timing samples, and a tested
watchdog/deadman/stop/exact-return harness. Reviewer 283 routes T19.2a to build
the target and motion-harness contracts offline. No additional hardware access
or actuation occurred; no Brev or paid compute was used.
