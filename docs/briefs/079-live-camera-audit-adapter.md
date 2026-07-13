# Slice Brief 079 - Live Camera Audit Adapter

**Date:** 2026-07-13

## Objective

Correct the reproduced live-only mismatch between the rich finite FFmpeg
backend audit and the exact static-pose camera lifecycle audit.

## Reproduced failure

The pinned camera passed frame normalization, then returned the generic
backend's exact subprocess, mode, identity, delivery, and cleanup audit. The
static-pose runtime deliberately accepts only open/read/release counts plus
three prohibited-operation counters, so it rejected the richer dictionary.

## Contract

- Adapt only `PinnedFFmpegStaticPoseCamera.audit()`.
- Require the exact successful finite FFmpeg audit, including camera identity,
  reviewed mode, one start/communicate/wait lifecycle, two delivered frames,
  one release, no terminate/kill, and zero property writes or continuous
  recording.
- Project that validated audit to the exact static-pose open/read/release and
  prohibited-operation fields; reject missing, unknown, boolean, or drifted
  values.
- Add a deterministic red test before implementation, then run the full proof
  ladder and broad authority/twin gate.

The live gate remains closed. This slice grants no session, observation, model,
motion, training, or paid-compute authority.
