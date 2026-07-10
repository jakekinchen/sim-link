# Executor Session 010 - Frame-Level Policy Tasks

**Date:** 2026-07-10

## Slice

Complete T10.4 by retaining the exact language prompt supplied to PI0.5 for
every policy proposal and exported expert correction.

## Result

- Neural rollout frames now record `policy_task` before inference.
- Controller-executed correction frames retain the prompt that conditioned the
  policy proposal they replace.
- Both compact and audit-schema exporters use the frame prompt as the LeRobot task.
- DAgger export rejects legacy frames without an exact prompt; non-DAgger test
  exports may still use the explicit episode task fallback.

## Verification

49 intervention/autolearn tests pass, including exact prompt use and missing-label rejection.

## Proof Boundary

Existing bootstrap trajectories cannot be retroactively called exact-task data.
They must be recollected under the new logger.

## Next Step

T10.5 merge-contract enforcement and corrected collection/export/merge canary.
