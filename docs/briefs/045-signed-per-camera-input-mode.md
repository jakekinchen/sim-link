# Slice Brief 045 - Signed Per-Camera Input Mode

**Date:** 2026-07-11

## Objective

Correct the exact camera-input gap exposed by rejected live attempt 004. Bind a
supported input pixel format to each exact-name/system-identity camera rather
than relying on AVFoundation's default `yuv420p`. Source every selection from
signed, normalized supported-mode metadata and carry it through the execution
contract, ffmpeg command, audit, diagnostics, and private/tracked evidence. Keep
`live_gate` closed throughout implementation and review.

## Evidence basis

- Attempt 004 private failure identity:
  `785241af1d0ccc6c06a5a71cf2a1cf5f91073b91704d83402b15ce313a8fd4cb`.
- Diagnostic identity:
  `bd722dd787dd7b4f26aa9735dd8c5d0e78aed9551d5aedf45f4caa799c86aab9`.
- The first camera subprocess returned zero at exact 30 fps but emitted 339
  stderr bytes because selected `yuv420p` was unsupported. It advertised
  `uyvy422`, `yuyv422`, `nv12`, `0rgb`, and `bgr0`.
- The second camera's supported input modes were not observed by attempt 004.
  Do not infer or copy the first camera's mode to it.

## Supported-mode discovery contract

- Version the live discovery representation so each system camera may carry a
  normalized, finite supported-input-mode set bound to its exact name,
  `unique_id`, and `model_id`.
- Production mode metadata must come from bounded camera-device metadata
  enumeration without starting a frame stream. Offline tests use injected
  recorded outputs only; Brief 045 itself performs no live enumeration.
- Normalize pixel format, dimensions, and frame-rate bounds; reject duplicates,
  non-finite values, unknown formats, identity ambiguity, empty mode sets,
  inconsistent duplicate records, and mode substitution across cameras.
- Preserve verification for legacy rejected discovery/failure evidence without
  allowing legacy discovery to prepare a new live contract.

## Exact input-mode contract

- Version the execution contract and require one exact supported input mode per
  selected camera. Selection must be a member of that camera's signed supported
  set and may not be inferred from another camera.
- Place exact `-pixel_format`, `-video_size`, and `-framerate` options before
  the corresponding AVFoundation input. Reject missing, reordered, duplicated,
  post-input, unsupported, or cross-camera-substituted options.
- Bind the selected mode into the backend audit, failure diagnostic, private
  success/failure evidence, and redacted manifest. Preserve strict stderr,
  nonzero, timeout, PNG, frame-count, and cleanup rejection.

## Validation

- Add deterministic format-normalization, per-camera selection, command-order,
  audit/evidence linkage, legacy verification, and coordinated resigned-tamper
  tests using only fixture/recorded metadata.
- Run focused tests under both local runtimes, both offline verifiers,
  deterministic disconnect/census verification while the gate is closed,
  `py_compile`, privacy/diff checks, and the broad robot-lab gate.
- Fresh same-agent adversarial review, explicit-path implementation commit and
  push, canonical closeout commit and push, then a separate live-gate decision.

## Authority

Offline implementation only. No metadata discovery, serial/camera open, Studio
request, reconnect, signal, configuration/register write, torque change,
motion, policy actuation, proof label, physical qualification, optimizer, paid
compute, merge/rebase/force-push, or destructive action. `training_lock` and
`live_gate` remain closed.
