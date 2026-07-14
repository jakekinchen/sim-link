# Slice Brief 136 - T20.16 Hybrid Gripper Postprocessor Rollout

**Date:** 2026-07-14

## Objective

Falsify the T20.15 channel-local hypothesis by retaining checkpoint state and
arm action scaling while substituting only T20.13 gripper action statistics.

## Contract

- Re-hash T20.10, T20.13, T20.14, T20.15, the seed-2 source episode, and the
  T20.14 adapter. Require live simulation-inference authority before model
  load and each model call.
- Deep-copy the pinned checkpoint processor. Change only action index 5 mean
  and standard deviation in the postprocessor; retain checkpoint state
  preprocessing and action indices 0-4 byte-for-byte.
- First reproduce the T20.15 predicted frame-zero arm MAE near 0.03088 rad and
  gripper error near 0.12015 rad. Fail before rollout if either differs by more
  than 1e-6 rad.
- Then run the fixed seed-2 T20.10 force-bearing strict loop with 244
  policy-owned frames, five 256 px keyframes, action tracing, projection and
  assistance accounting, and every measured-versus-threshold margin.

## Acceptance Criteria

- Processor isolation, frame-zero prediction, source/checkpoint binding, and
  deterministic runtime all pass without optimizer or checkpoint mutation.
- The strict rollout and rendered stages determine the result. A frame-zero
  improvement alone is not capability evidence and cannot accept a policy.
- Tests and same-agent review reject arm-stat drift, state-preprocessor drift,
  hidden clipping, source swaps, missing keyframes or margins, non-finite
  values, hardware access, external compute, and authority escalation.

## Out Of Scope

Training, loss changes, more seeds, model-family changes, hardware, physical
transfer, promotion, external compute, and Brev.
