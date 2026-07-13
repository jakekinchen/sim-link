# Session 109 - Live Camera Audit Adapter

**Date:** 2026-07-13

Brief 079 reproduced the rejected live-only boundary as a deterministic failing
test. The generic finite FFmpeg backend returns exact camera identity and mode,
subprocess start/communicate/wait/terminate/kill counts, frame deliveries,
release counts, and forbidden-operation counts. The strict static-pose runtime
accepts an exact open/read/release lifecycle view.

The correction is confined to `PinnedFFmpegStaticPoseCamera.audit()`. It
requires the exact successful two-frame FFmpeg lifecycle, detects boolean and
all other value drift through canonical comparison, and returns only the exact
static-pose audit fields. The targeted test failed before implementation and
passes after it.

Verification passed 181 focused tests in each pinned runtime, 380 broad
authority/twin tests in 131.297 seconds, both source verifiers in both runtimes,
compilation, the workflow audit, and diff checks. No hardware, model, MuJoCo,
motion, training, Brev, or paid compute ran; the consumed gate remained closed.
