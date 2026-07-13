# Slice Brief 087 - Current Physical Preprocessing, Shadow, And Replay Diagnostic

**Date:** 2026-07-13

## Objective

Execute the shortest no-actuation diagnostic chain allowed by Reviewer 112 on
the accepted current bracket, then mechanically accept or reject policy-shadow
and matched-replay suitability without weakening any physical gate.

## Contract

- Bind private-success v2 session `t16-5c-20260713-0958-cdt`, final frame index
  1 for each stable camera identity, the reviewed external/wrist role mapping,
  exact `q_after`, and the exact sorting-checkpoint prompt.
- Run the pinned real PI0.5 processor and model-image boundary strictly offline;
  require deterministic tensor hashes and preserve the current scene mismatch.
- Load only checkpoint revision `84b551af...` locally on MPS, require the exact
  8.7 GB weight hash and strict state-dict success, and produce one finite
  fixed-noise proposal twice with exact equality.
- Postprocess the complete 50x6 absolute LeRobot action chunk and compare it to
  the measured pose without sending any action.
- Replay prefixes 5, 10, and 15 independently at 10 Hz in the canonical
  sorting MuJoCo scene, recording coordinate projection, joint state, velocity,
  contacts, object displacement, warnings, and exact determinism.
- Treat preprocessing, inference, and replay as diagnostic evidence only. Fail
  closed on out-of-support state, visual/task mismatch, coordinate projection,
  collision, large deltas, or any non-finite/nondeterministic result.

This slice may record exact current physical model-ready tensors, a real local
no-actuation proposal, and deterministic proposal-prefix control replays. It
must not grant accepted live policy input, accepted policy shadow, matched
MuJoCo replay, positive actuation recommendation, motion, training, physical
twin qualification, or paid compute.
