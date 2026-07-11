# Slice Brief 044 - Explicit Camera Mode And Failure Servo Evidence

**Date:** 2026-07-11

## Objective

Correct the two offline evidence gaps exposed by rejected live attempt 003.
Bind the retained AVFoundation-supported 30 fps mode into the exact live
execution contract, ffmpeg command, and backend audit. Preserve the complete
verified live servo result inside any private camera-failure artifact so a
rejected camera stage cannot discard the six per-servo `Torque_Enable` values
or their exact transport trace. Keep `live_gate` closed throughout.

## Evidence basis

- Attempt 003 diagnostic identity:
  `482064ad86290cfcf7f92469a68c7e0376b501896465f63a5ad1aaccb9d459e3`.
- ffmpeg returned 251 after AVFoundation selected unsupported 29.970030 fps.
- The bounded diagnostic states that 30.000030 fps is supported. Use the
  integer request `30`; do not infer a size, pixel format, or second-camera mode
  from unobserved evidence.
- The no-write census completed 54 successful reads, zero retries, and a
  successful no-torque close, but failure schema v2 retained only the servo
  result identity and counts rather than the full result.

## Camera-mode contract

- Version the live execution contract and add an exact integer
  `camera_framerate_fps=30` field.
- Require the named ffmpeg backend to place `-framerate 30` before the
  AVFoundation `-i` input and expose the same value in its audit.
- Reject missing, boolean, non-integer, non-30, reordered, duplicated, or
  post-input framerate arguments and any audit/contract mismatch.
- Retain exact-name camera binding, finite frame count, timeout, full PNG
  validation, strict stderr/nonzero rejection, and subprocess cleanup.

## Failure servo evidence

- Version the private capture-failure schema and embed the complete signed live
  execution contract plus complete signed live servo result.
- Independently replay and verify the embedded read trace against the embedded
  census contract; require exact identities, operation counts, target identity,
  all six decoded servos, all six `Torque_Enable=0` values, no-write close, and
  `physical_follower_commanded=false`.
- Reject missing or substituted contract/result, resigned trace/result drift,
  nonzero torque, count mismatch, and evidence identity substitution.
- Keep failure artifacts ignored/private, label-free, immutable, and distinct
  from any tracked success manifest.

## Validation

- Focused tests for command ordering, exact framerate binding, fake success,
  retained failure evidence, full servo-result tampering, nonzero torque, holder
  snapshots, cleanup, privacy, and all existing adversarial camera cases.
- Both offline runtime verifiers, deterministic census and disconnect-proof
  verification while the gate is closed, `py_compile`, `git diff --check`, and
  the broad robot-lab regression gate.
- Fresh same-agent review, explicit-path implementation commit and push,
  canonical closeout commit and push, then a separate live-gate decision.

## Authority

Offline implementation only. No metadata discovery, serial or camera open,
Studio request, reconnect, process signal, register/configuration write, torque
change, motion, policy actuation, proof label, physical qualification,
optimizer, paid compute, merge/rebase/force-push, or destructive action.
`training_lock` and `live_gate` remain closed.
