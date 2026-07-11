# Reviewer Decision 062 - Reject Live Attempt 003 Framerate Failure

**Date:** 2026-07-11

## Decision

`REJECT LIVE ATTEMPT 003; KEEP LIVE GATE CLOSED; CONTINUE OFFLINE WITH BRIEF 044`

## Evidence

- Session: `t16-5b-20260711-1005-cdt`.
- Discovery: `7a187d11f43aad4032b54c9c6e35f99b327002e2edd3a01d0aed48966a73f0bd`.
- Contract: `63979ed40e4597bc75ce681b95febb22bdfc9982c6e72394ac60550caa3923f7`.
- Presence lease:
  `527ad75402a25ffdd77d025596bca9e344b63b03baaa464ee89b378c5d767075`.
- Private failure:
  `e7f8eb21e531a8013a034cb53a8c9f93713039c63d44932bd5d51e0c53c25714`.
- Camera diagnostic:
  `482064ad86290cfcf7f92469a68c7e0376b501896465f63a5ad1aaccb9d459e3`.

## Review

Fresh metadata discovery opened no device. Both signed serial paths were free
before lease creation and immediately before bus open. The exact census then
completed 54 successful allowlisted reads with zero retries, zero writes,
zero torque changes, zero motion commands, and one successful
`disable_torque=false` close. The post-close signed holder snapshots remained
zero across both paths.

The first exact-name camera subprocess returned 251 before delivering a frame.
The retained bounded stderr states that AVFoundation selected unsupported
29.970030 fps and advertises 30.000030 fps. Release succeeded, no ffmpeg process
remained, the post-failure all-alias holder check remained zero, and no tracked
success manifest was created.

The private failure artifact verifies and binds the servo-result identity and
operation counts, but schema v2 does not embed the complete servo result. The
attempt therefore grants neither `live_read_only_census_observed` nor
`physical_observation_capture`, even though the in-process census gate had to
pass before camera execution. Proof labels remain empty and
`physical_follower_commanded=false`.

The initial MuJoCo-venv command failed on missing `pyserial` before enumeration
or artifact creation. Reusing the same session ID with the already-pinned
LeLab runtime was an invocation correction, not a second live session.

Brief 044 may proceed offline to contractually request 30 fps and retain the
complete servo result in future private camera-failure evidence. No additional
live session is authorized by this decision.
