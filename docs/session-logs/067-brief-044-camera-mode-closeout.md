# Session 067 - Brief 044 Camera Mode Closeout

**Date:** 2026-07-11

Brief 044 implementation `4ae0521c1c34279b1464c151988ee5ae19e2fd7d` is
present locally, upstream, and on `origin/codex/pi05-autolearn-loop`. It versions
the live contract to v2, binds integer 30 fps, places exactly one
`-framerate 30` before the AVFoundation input, and binds the mode into v2
diagnostics plus v3 private/tracked success evidence.

Future v3 private camera-failure evidence embeds the complete signed execution
contract and live servo result. Its public verifier reconstructs the transport
trace and checks all six decoded `Torque_Enable=0` values, target identity,
counts, no-write close, camera identity/mode, and both signed holder snapshots.
Attempt 003's v1 diagnostic and v2 private failure continue to verify.

The installed runtime is FFmpeg 8.0.1 and reports AVFoundation's default
framerate as `ntsc`. FFmpeg's AVFoundation source selects a range when the
absolute requested/max-rate difference is below 0.01 fps. Integer 30 differs
from attempt 003's advertised 30.000030 by 0.000030 fps, so the correction is
within the production matcher without guessing size or pixel format. Source:
`https://github.com/FFmpeg/FFmpeg/blob/master/libavdevice/avfoundation.m`.

Verification: 50 focused tests; 30 camera tests under the pinned LeLab runtime;
229 broad tests in 76.974 seconds; both offline runtime verifiers; deterministic
disconnect-proof and census-fixture verification; legacy attempt-003 private
artifact verification; `py_compile`; and `git diff --check`.

No metadata discovery, serial/camera open, Studio request, reconnect, signal,
register/configuration write, torque change, motion, policy actuation, proof
label, physical qualification, optimizer, paid compute, or destructive action
occurred. `training_lock` and `live_gate` remain closed pending a separate live
gate review commit.
