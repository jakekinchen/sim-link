# Session 070 - Brief 045 Per-Camera Mode Closeout

**Date:** 2026-07-11

Brief 045 implementation `820a40f0339ccd1c5cfd71789bbea6cdf1b4f036` is
present locally, upstream, and on `origin/codex/pi05-autolearn-loop`.

Discovery v2 adds signed normalized per-camera pixel formats, dimensions, and
finite rate ranges sourced from `AVCaptureDevice.formats` without a capture
session or frame stream. Contract v3 chooses the smallest reviewed mode that
supports integer 30 fps within 0.01 fps. The FFmpeg backend places exact
`-pixel_format`, `-video_size`, and `-framerate` arguments before the exact-name
input and records the same mode in its audit.

Diagnostic v3, private success/failure v4, and tracked manifest v4 bind the
mode. Discovery v1 cannot authorize a new contract, while attempt 003's v2 and
attempt 004's full v3 private failures remain verifiable. Cross-camera,
coordinated resigned, malformed, duplicate, non-finite, unknown-format, and
command-order substitutions fail closed.

Verification: 52 focused tests; 32 camera tests under the pinned LeLab runtime;
231 broad tests in 74.938 seconds; both offline verifiers; Swift source
typecheck; legacy artifact verification; `py_compile`; authority-surface,
privacy, and diff checks.

No metadata discovery, serial/camera open, Studio request, reconnect, signal,
register/configuration write, torque change, motion, policy actuation, proof
label, physical qualification, optimizer, paid compute, or destructive action
occurred. `training_lock` and `live_gate` remain closed pending a separate gate
review commit.
