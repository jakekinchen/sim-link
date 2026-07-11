# Reviewer Decision 058 - Reject Live Attempt 002 Camera Subprocess

**Date:** 2026-07-11

## Decision

`REJECT ATTEMPT 002; RECLOSE LIVE GATE; OPEN BRIEF 042 OFFLINE`

## Evidence anchor

`100 - Fail-closed capture with incomplete failure diagnostics`

## Review

- Attempt 002 used a new discovery, lease, and contract; rejected attempt 001
  was not reused.
- The runtime reached camera capture only after the read-only census closed and
  the reviewed post-close holder check passed.
- The first exact-name ffmpeg subprocess returned nonzero. Strict capture code
  rejected it and cleanup left no ffmpeg process.
- Follower status remains disconnected with torque false; the exact holder list
  remains empty; the leader remains connected.
- No private evidence bundle, tracked manifest, or proof label was written.
- `physical_follower_commanded=false`; there was no motion, policy actuation,
  general register write, physical qualification, or training.
- The current production exception discards stderr on a nonzero return code.
  Without bounded sanitized text or a digest, the failure cannot be classified
  mechanically and should not be retried blindly.

Brief 042 must remain offline: preserve strict nonzero/stderr rejection while
retaining bounded sanitized diagnostic evidence, add deterministic truncation,
digest, non-UTF8, timeout, cleanup, and no-success-leak tests, and keep the live
gate closed until that correction is reviewed and remotely preserved.
