# Reviewer Decision 063 - Brief 044 Camera Mode Reviewed

**Date:** 2026-07-11

## Decision

`ACCEPT BRIEF 044 OFFLINE; KEEP LIVE GATE CLOSED FOR A SEPARATE REVIEW COMMIT`

## Evidence anchor

`4ae0521c1c34279b1464c151988ee5ae19e2fd7d`

## Review

- The v2 live execution contract requires an exact non-boolean integer 30 fps.
  Missing, string, boolean, or other numeric values reject.
- The production command contains exactly one `-framerate 30` before the
  AVFoundation `-i`. The backend audit, v2 failure diagnostic, v3 private
  success evidence, and v3 redacted manifest bind the same value.
- Integer 30 is justified by attempt 003's advertised 30.000030 mode and
  FFmpeg AVFoundation's less-than-0.01 fps rate comparison; the difference is
  0.000030 fps. No unsupported video size or second-camera mode is inferred.
- V3 private camera-failure evidence embeds the full signed execution contract
  and full signed live servo result. Verification independently replays the
  exact read sequence, decoded values, all six `Torque_Enable=0` readings,
  operation counts, target identity, no-write close, camera identity/mode, and
  all-alias holder snapshots.
- Resigned torque, decoded-result, execution-contract, camera-mode, identity,
  count, missing-result, and audit substitutions reject. Attempt 003's v1
  diagnostic and v2 private failure remain verifiable.
- Cleanup, strict nonzero/stderr/timeout/PNG rejection, label-free private
  failures, privacy separation, and `physical_follower_commanded=false` remain
  unchanged. No global authority is added.

Verification: 50 focused tests; 30 camera tests under the pinned LeLab runtime;
229 broad robot-lab tests in 76.974 seconds; both offline runtime verifiers;
deterministic disconnect-proof and census-fixture verifiers; legacy attempt-003
artifact verification; `py_compile`; and `git diff --check`.

No hardware was enumerated or opened during Brief 044. No Studio request,
reconnect, process signal, register/configuration write, torque transition,
motion, policy actuation, physical qualification, optimizer, paid compute, or
destructive action occurred. A new live session requires a separate reviewed,
scoped, pushed, and remotely confirmed gate transition.
