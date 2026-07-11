# Session 069 - Rejected Live Attempt 004 Pixel Format Failure

**Date:** 2026-07-11

Reviewer 064's one-session gate was remotely confirmed at `26a2824`. Fresh
discovery `2e63871a...` found four serial candidates and two named/system-bound
cameras while opening neither. Both signed follower paths existed and were
holder-free before the five-minute lease.

V2 contract `b9b3c7ec...` and lease `f993a7c7...` were valid from
`2026-07-11T10:37:14-05:00` through `2026-07-11T10:42:14-05:00` and bound exact
30 fps. Servo result `f5c6d17e...` completed 54 reads with zero retries, writes,
torque changes, motion commands, or unexpected operations. All six servos
reported model 777 and `Torque_Enable=0`; no-torque close succeeded. Pre-open,
post-close, and post-failure holder checks observed `[0,0]`, deduplicated zero,
with snapshot `b33a7cc0...`.

The first exact-name camera returned zero but strict stderr handling rejected
339 bytes, hash `80b01de5...`. Diagnostic `bd722dd7...` reports unsupported
default `yuv420p` and supported `uyvy422`, `yuyv422`, `nv12`, `0rgb`, and
`bgr0`. It retained 5,244,174 stdout bytes by hash `11bcb1c0...`; no frame was
accepted. Release succeeded and no ffmpeg process remained.

V3 private failure `785241af...`/file `305c42fb...` is 40,640 bytes and
independently verifies the full contract, complete servo result, exact trace,
camera diagnostic, and both holder snapshots. No success bundle, tracked
manifest, or proof label was written. The gate reclosed at
`2026-07-11T10:37:42-05:00`.

The follower was not reconnected. No Studio request, signal,
configuration/register write, torque transition, motion, policy actuation,
physical qualification, optimizer, paid compute, or destructive action
occurred. Brief 045 owns the offline exact per-camera supported-mode correction.
