# Session 106 - Live Frame Metadata Adapter

**Date:** 2026-07-13

Brief 076 reproduced the rejected live-only boundary as a deterministic failing
test. `FFmpegNamedFiniteCamera` returns five semantic PNG fields plus exact
batch receive start/finish timestamps; the strict static-pose normalizer owns
its own per-read interval and accepts exactly the five semantic fields.

The correction is confined to `PinnedFFmpegStaticPoseCamera.read()`. It
requires the exact seven fields, rejects missing/unknown fields and boolean,
negative, or non-increasing receive timestamps, and returns only the unchanged
five semantic fields. The targeted test failed before implementation and passes
after it.

Verification passed 79 focused tests in each pinned runtime, 379 broad
authority/twin tests in 124.646 seconds, both source verifiers in both runtimes,
compilation, and diff checks. No hardware, model, MuJoCo, motion, training,
Brev, or paid compute ran; the consumed gate remained closed.
