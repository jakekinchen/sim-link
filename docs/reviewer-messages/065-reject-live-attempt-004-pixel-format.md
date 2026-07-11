# Reviewer Decision 065 - Reject Live Attempt 004 Pixel Format Failure

**Date:** 2026-07-11

## Decision

`REJECT LIVE ATTEMPT 004; KEEP LIVE GATE CLOSED; CONTINUE OFFLINE WITH BRIEF 045`

## Evidence

- Session: `t16-5b-20260711-1036-cdt`.
- Discovery: `2e63871a0dccd403e02e337741593e8e108f82685d08e6ce5f6c177d76bb8f77`.
- Contract: `b9b3c7ecf70cadc269fd703e81df18fea56669fa7e40db6d7c721f87b8e2a358`.
- Presence lease:
  `f993a7c714c39ce3e47c3ac7f3963478efc0aff26d08813776cbae87d0b581dd`.
- Private failure:
  `785241af1d0ccc6c06a5a71cf2a1cf5f91073b91704d83402b15ce313a8fd4cb`.
- Servo result:
  `f5c6d17e61ed09f6b84a5a40d9545cc95661b292e0e63055f98e6384c686fd34`.
- Camera diagnostic:
  `bd722dd787dd7b4f26aa9735dd8c5d0e78aed9551d5aedf45f4caa799c86aab9`.

## Review

Fresh discovery opened no device and found the same four serial candidates and
two exact-name/system-identity cameras. Both signed follower paths existed and
had zero holders before lease creation, immediately before bus open, after
no-write close, and after failure.

The exact v2 contract bound integer 30 fps. The live census completed 54
successful allowlisted reads with zero retries, zero register/configuration
writes, zero torque changes, zero motion commands, and one successful
`disable_torque=false` close. The complete signed v3 private failure independently
replays that result and records all six model-777 servos with
`Torque_Enable=0`.

The first exact-name camera subprocess returned zero but emitted 339 stderr
bytes. Its bounded diagnostic says AVFoundation selected unsupported default
`yuv420p` and advertises `uyvy422`, `yuyv422`, `nv12`, `0rgb`, and `bgr0`. The
second camera's modes were not observed and must not be inferred. Release
succeeded, no ffmpeg process remained, and the post-failure all-alias holder
check remained zero.

Strict stderr rejection is correct. No private success bundle, tracked success
manifest, or proof label was written. The embedded servo result is verified
local evidence from a rejected session; it does not grant the outer session
`live_read_only_census_observed` or `physical_observation_capture` label.
`physical_follower_commanded=false`.

Brief 045 may proceed offline to bind exact per-camera supported-mode metadata
and pre-input mode arguments. No additional live session is authorized by this
decision.
