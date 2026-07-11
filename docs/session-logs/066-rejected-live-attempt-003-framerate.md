# Session 066 - Rejected Live Attempt 003 Framerate Failure

**Date:** 2026-07-11

Reviewer 061's one-session gate was remotely confirmed at `37fced95`. The
MuJoCo test venv first failed to import `pyserial` before enumeration or artifact
creation; the same session ID then used the pinned LeLab runtime. Fresh metadata
discovery `7a187d11...` found four serial candidates and two named cameras while
opening neither. Both signed follower paths were holder-free.

Contract `63979ed4...` and presence lease `527ad754...` were valid from
`2026-07-11T10:06:30-05:00` through `2026-07-11T10:11:30-05:00`. The live
census completed 54 successful reads with zero retries, zero writes, zero torque
changes, zero motion commands, and one successful no-torque close. Pre-open,
post-close, and post-failure holder checks all observed `[0, 0]`, deduplicated
zero, with snapshot identity `b33a7cc0...`.

The first named-camera subprocess returned 251 and delivered zero frames.
Private failure artifact `e7f8eb21...`/file `6148b56e...` retained diagnostic
`482064ad...`, 13,548 stderr bytes, full stderr digest `64a8d5ff...`, and a
2,048-byte sanitized preview. The preview identifies unsupported selected
29.970030 fps and advertised 30.000030 fps. Camera release succeeded, no ffmpeg
process remained, no success bundle or tracked manifest was written, and no
proof label was granted.

The live gate was reclosed at `2026-07-11T10:07:17-05:00`. The follower was not
reconnected; no Studio request, process signal, configuration/register write,
torque transition, motion, policy actuation, physical qualification, optimizer,
paid compute, or destructive action occurred. Brief 044 owns the offline
explicit-framerate and complete failure-servo-evidence correction.
