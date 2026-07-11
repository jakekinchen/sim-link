# Slice Brief 046 - Exact Camera Output Dimensions

**Date:** 2026-07-11

## Objective

Correct the verifier gap exposed by rejected live attempt 005. Require every
decoded PNG frame to have the exact width and height selected in that camera's
signed input mode. Reject dimension drift inside the named-camera capture path
before private-success or tracked-manifest construction, and independently
recheck it in private evidence verification. Keep `live_gate` closed.

## Evidence basis

- Attempt 005 private candidate identity:
  `ebb4934c18ef77bb5563800a0cea36a847b1568e8c0ce03bd397ff0eb0036671`.
- Candidate manifest identity:
  `0d7b4400ccd5f926176ae083be37c33824d59753ffeb186adcd46d663b723da3`.
- Camera 0 requested and produced `160x90`.
- Camera 1 requested `424x240` but both PNGs decoded as `640x480`.
- The current v4 verifier accepted the candidate because it validates PNG
  structure and command/audit mode but does not compare decoded dimensions to
  the signed camera input mode.

## Contract enforcement

- The named FFmpeg backend must compare every parsed PNG's width and height to
  its exact signed input mode before returning any frame.
- A mismatch raises a bounded `png_validation` failure, releases the subprocess,
  and produces label-free private failure evidence with the full contract and
  servo result.
- `_verify_captured_frames`, private-success construction, and redacted-manifest
  construction independently require exact per-camera dimensions.
- Reject mixed dimensions within one batch, cross-camera dimension swaps,
  coordinated resigned mode/frame metadata substitution, and manifest-only
  dimension substitution.
- Preserve output RGB PNG encoding, strict stderr/nonzero/timeout rejection,
  frame hashing, all-alias holder evidence, no-write close, cleanup, and legacy
  rejected-artifact verification.

## Validation

- Add deterministic tests for exact match and every dimension-drift path using
  fixture PNGs only.
- Run focused tests under both runtimes, both offline verifiers, deterministic
  disconnect/census verification, legacy attempt-003/004 verification,
  `py_compile`, privacy/diff checks, and the broad robot-lab gate.
- Fresh same-agent review, explicit implementation commit/push, canonical
  closeout commit/push. Any later live gate remains a separate decision.

## Authority

Offline implementation only. No metadata discovery, serial/camera open, Studio
request, reconnect, signal, configuration/register write, torque change,
motion, policy actuation, proof label, physical qualification, optimizer, paid
compute, merge/rebase/force-push, or destructive action. `training_lock` and
`live_gate` remain closed.
