# Reviewer Decision 066 - Brief 045 Per-Camera Mode Reviewed

**Date:** 2026-07-11

## Decision

`ACCEPT BRIEF 045 OFFLINE; KEEP LIVE GATE CLOSED FOR A SEPARATE REVIEW COMMIT`

## Evidence anchor

`820a40f0339ccd1c5cfd71789bbea6cdf1b4f036`

## Review

- Discovery v2 binds normalized supported modes to exact camera name,
  `unique_id`, and `model_id`. Production metadata reads
  `AVCaptureDevice.formats` without constructing `AVCaptureSession` or starting
  a frame stream. Empty, mismatched, duplicate, unknown, non-finite, impossible,
  or unnormalized records reject.
- Contract v3 selects only from each camera's own signed modes. It chooses the
  smallest frame area, then reviewed pixel-format priority, and requires integer
  30 fps to match the signed range within the existing 0.01-fps AVFoundation
  tolerance. Legacy discovery v1 cannot prepare a new contract.
- The named FFmpeg command contains exactly one `-pixel_format`, `-video_size`,
  and `-framerate` before input. Input values are whitelist-derived, not string-
  injected, and the output remains finite RGB PNG.
- Backend audits, diagnostic v3, private success v4, private failure v4, and
  tracked manifest v4 bind the selected input mode. Coordinated resigned
  cross-camera contract/diagnostic/result substitutions reject.
- Attempt 003's v2 and attempt 004's v3 private failure artifacts remain
  verifiable. Strict stderr/nonzero/timeout/PNG rejection, bounded diagnostics,
  label-free failures, all-alias holder checks, no-write close, and cleanup are
  unchanged.

Verification: 52 focused tests; 32 camera tests under the pinned LeLab runtime;
231 broad robot-lab tests in 74.938 seconds; both offline runtime verifiers;
Swift metadata-source typecheck; legacy artifact verification; `py_compile`;
static authority-surface and privacy review; and `git diff --check`.

No hardware was enumerated or opened during Brief 045. No Studio request,
reconnect, process signal, register/configuration write, torque transition,
motion, policy actuation, physical qualification, optimizer, paid compute, or
destructive action occurred. A new live session requires a separate reviewed,
scoped, pushed, and remotely confirmed gate transition.
