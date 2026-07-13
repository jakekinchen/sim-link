# Slice Brief 084 - Retain Private Current Camera Frames

**Date:** 2026-07-13

## Objective

Correct the concrete post-capture gap exposed by the accepted physical bracket:
retain the exact current camera PNG bytes in private success evidence so they can
be source-bound to the bracket and consumed by real PI0.5 preprocessing.

## Contract

- Preserve the existing candidate result, receipt, and redacted review manifest
  as hash-only artifacts.
- Add a backward-compatible private-success evidence version that contains
  exactly two frames for each of the two selected stable camera identities.
- Validate strict base64, byte bounds, PNG semantics, dimensions, channels,
  frame indexes, and hashes against the accepted candidate result.
- Capture bytes only after the pinned FFmpeg reader's exact metadata and audit
  contracts pass.
- Keep verification of existing v1 private successes and the accepted session
  `t16-5c-20260713-0912-cdt` unchanged.
- Ensure the redacted reviewer accepts verified v1 or v2 private evidence but
  never copies private frame bytes into tracked artifacts.

This correction may grant only
`private_source_bound_current_frame_retention_conformant`. It does not grant an
accepted live policy input, preprocessing, model loading, inference, replay,
motion, qualification, training, or paid compute. A new finite physical bracket
under a separately reviewed gate is required to create usable current frames.

## Test Plan

- Add a deterministic failing test for v2 byte/hash/source verification before
  implementation.
- Cover tampered bytes, camera/source mismatch, frame metadata mismatch, and
  backward-compatible v1 verification.
- Run the focused T16.5c suite in both pinned runtimes, both source verifiers,
  the broad authority/twin regression, compile checks, and diff checks.

## Out Of Scope

- Hardware access or camera capture.
- PI0.5 preprocessing, model loading, inference, or replay.
- Changes to camera-role or task-prompt semantics.
- Motion, torque, register writes, training, Brev, or paid compute.
