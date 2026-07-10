# Executor Session 020 - Bounded Evaluation Runtime

**Date:** 2026-07-10

## Slice

Complete T12.5 and close M12 by bounding evaluation image retention while keeping
training collection lossless and reusing a loaded policy service across seeds.

## Result

- Evaluation renders fresh live images every control step but overwrites three
  rolling files and retains snapshots only at a configured stride.
- Collection remains stride 1; exporter rejects any selected frame without a
  retained synchronized image, preventing sparse evaluation data from entering training.
- Episode/batch summaries record retention stride, retained frames, PNG count/
  bytes, server start count, checkpoint/device, and multi-episode reuse.
- Stage metrics are independent of retention and continue to use state/contact data.
- Transport now requires lift or at least 5 cm displacement plus tray proximity,
  eliminating an initial-position false positive found by the canary.

## Verification

- 66 intervention/autolearn tests pass.
- A 120-frame strict MPS canary retained four observation frames and produced 18
  total PNGs/1,542,965 bytes including rolling, scene, and final renders.
- Full retention would require at least 360 observation PNGs for the same rollout.
- A two-seed MPS canary started/loaded the policy server exactly once and reused it
  across both episode resets; the batch manifest records this explicitly.
- Both canaries remained strict, failed terminally as expected, and commanded no hardware.

## Proof Boundary

One-step warm-service episodes prove lifecycle reuse, not task competence. Sparse
retention changes durable audit images, never the observations supplied to policy.

## Next Step

T13.1 corrected 250/500/1,000-update MPS training ladder.
