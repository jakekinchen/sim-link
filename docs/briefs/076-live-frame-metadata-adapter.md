# Slice Brief 076 - Live Frame Metadata Adapter

**Date:** 2026-07-13

## Objective

Correct the reproduced live-only mismatch between
`FFmpegNamedFiniteCamera.read()` and the strict static-pose frame normalizer.

## Reproduced failure

The generic FFmpeg reader returns the five semantic frame fields plus bounded
batch receive start/finish timestamps. The static-pose runtime owns its own
per-read monotonic interval and intentionally accepts exactly the five semantic
fields, so the pinned live adapter passed two known lower-level fields through
and caused the consumed session to reject.

## Contract

- Adapt only `PinnedFFmpegStaticPoseCamera.read()`.
- Require the exact five semantic fields plus the exact two known receive-time
  fields from the pinned base reader; reject missing, unknown, boolean,
  negative, or non-increasing receive timestamps.
- Strip only those validated lower-level timestamps before returning the frame
  to the static-pose runtime; preserve bytes and semantic fields exactly.
- Add deterministic adapter tests, then run the full proof ladder and broad
  authority/twin gate.

The live gate remains closed. This slice grants no session, observation, model,
motion, training, or paid compute authority.
