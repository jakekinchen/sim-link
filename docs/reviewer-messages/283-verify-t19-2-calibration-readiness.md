# Reviewer Decision 283 - Verify T19.2 Calibration Readiness

**Date:** 2026-07-16

## Decision

`ACCEPT T19.2 READINESS MATRIX; CONTINUE WITH T19.2A TARGET AND BOUNDED-MOTION HARNESS`

Brief 213 implementation `a0d36045fa748f87eb129aaef023b645d1eb4636`
and fail-fast correction `9cfd5fd258c4e07387889c32025203a79c28d9fd`
are on origin. Signed report `5476d01d...` recomposes from the accepted T19.1
manifest, signed calibration semantics, reviewed camera-session identity,
offline timing fixture, and canonical T16.6/T19 state.

The report preserves four local facts: fresh servo identity/telemetry exists,
joint calibration semantics are source-bound, historical camera identity/mode
review exists, and offline timing thresholds are defined. It does not relabel
any of those as metric calibration. Eight prerequisites remain explicitly
missing: a central motion decision, current metric calibration target, measured
camera intrinsics, measured camera-to-base extrinsics, held-out joint-offset
motion samples, metric gripper-aperture samples, live monotonic timing samples,
and a verified watchdog/deadman/stop/exact-return harness.

Fresh adversarial review checked source substitution, state/artifact mismatch,
re-signed positive readiness, fixture-to-physical relabeling, stale camera
semantics, missing-evidence defaulting, nondeterministic ordering, authority
escalation, and non-finite/source drift. Four focused adversarial tests, exact
artifact verification, pointer tests, compilation, strict JSON, and diff checks
pass. No hardware, camera, serial, write, torque, motion, policy, optimizer,
external-compute, or Brev path ran.

The matrix grants only `t19_2_calibration_readiness_matrix_valid`. T19.2 remains
in progress. T19.2a must implement and fixture-test the calibration-target
contract plus the bounded watchdog/exact-return motion harness before any new
live gate can be proposed.
