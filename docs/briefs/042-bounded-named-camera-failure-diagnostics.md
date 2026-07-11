# Slice Brief 042 - Bounded Named-Camera Failure Diagnostics

**Date:** 2026-07-11

## Objective

Contain rejected T16.5b attempt 002 and make every production ffmpeg camera
failure mechanically classifiable without weakening the strict finite-capture
contract. Perform implementation and all tests offline. Do not open a serial
port or camera in this slice.

## Trigger and containment

- Fresh discovery `7766ed1c...`, lease `980b555c...`, and contract
  `51467ec7...` reached the first exact-name camera batch only after the
  read-only census closed and the post-close holder check passed.
- ffmpeg returned nonzero. `FFmpegNamedFiniteCamera` raised a generic exception
  and discarded stdout/stderr, return-code detail, and an inspectable failure
  audit, so contention, format negotiation, and backend/command faults cannot be
  distinguished.
- Cleanup left no ffmpeg process, follower holder count zero, follower
  disconnected/torque false, and leader connected.
- No private evidence bundle, tracked manifest, or proof label was written.
- Attempt 002 remains rejected permanently. Do not reuse its expired contract.

## Typed bounded diagnostic contract

- Introduce a typed camera-capture failure carrying a signed/canonical
  diagnostic object with a version, stage, camera identity hash, return code,
  stdout/stderr byte counts and SHA-256 digests, bounded sanitized stderr
  preview, subprocess lifecycle counts, and primary/cleanup error types.
- Bound captured stdout/stderr before any retained diagnostic. The preview must
  have an explicit byte/character maximum, decode malformed UTF-8 with a stable
  policy, normalize control characters, and state whether truncation occurred.
- Redact the exact camera name, unique ID, model ID, local paths, and serial-like
  tokens from the retained preview. Private ignored evidence may retain the
  bounded sanitized preview; tracked evidence may retain only hashes, counts,
  stages, error types, and truncation flags.
- Preserve the original exception as the primary cause. If cleanup also fails,
  retain both failures without replacing or suppressing either one.

## Failure-evidence lifecycle

- On a live CLI failure after contract verification, atomically write a signed
  ignored-private failure record under the requested session directory. It must
  bind the session, discovery, lease, contract, camera identity, bounded
  diagnostic, elapsed time, serial pre/post holder snapshots already observed,
  and `physical_follower_commanded=false`.
- A failure record is never an accepted observation bundle and must never emit
  the tracked success manifest or either live proof label.
- Enforce create-new paths, content addressing, no overwrite, and no partial
  success artifact if failure-record writing itself fails.
- Success semantics remain unchanged: nonzero exit, any stderr, timeout,
  malformed/truncated/extra PNG data, or trailing bytes all reject capture.

## Validation

- Deterministic fake-subprocess tests for nonzero exit, stderr-only rejection,
  malformed UTF-8, control characters, exact boundary and over-boundary
  truncation, camera-name/ID/path/token redaction, stdout/stderr digests, and
  return-code binding.
- Timeout, terminate/wait/kill, primary-plus-cleanup failure, and audit-count
  tests prove no orphan process and no swallowed error.
- Failure-record tests prove canonical signing, exact contract/session/holder
  binding, create-new/no-overwrite behavior, ignored-private placement,
  `physical_follower_commanded=false`, and absence of a tracked success
  manifest/proof labels.
- Existing named-camera, live-observation, T16.5a census, authority,
  qualification, twin, dependency-lock, LeRobot, `py_compile`, formatter, and
  `git diff --check` gates.
- Fresh same-agent adversarial review, explicit-path commits, push only to the
  named branch, and remote confirmation before any live-gate reconsideration.

## Authority

This brief is offline-only. It grants no metadata enumeration, serial/camera
open, process signal outside the fake capture under test, register write,
torque change, motion, reconnect, live proof label, physical qualification,
policy actuation, training, transfer, promotion, or global authority.
`training_lock` remains closed.
