# Executor Session 011 - Trusted PI0.5 Data Contract

**Date:** 2026-07-10

## Slice

Complete T10.5 and close M10 by enforcing machine-readable contracts at merge,
then recollecting and exporting one corrected MPS canary trajectory.

## Result

- Base, correction, and merged datasets carry content-addressed PI0.5 contracts.
- Merge rejects datasets without exact frame tasks, contiguous segmentation,
  canonical SO-101 coordinates, matching action representation, and matching FPS.
- The accepted base normalizer remains byte-identical in the merged dataset.
- Seed 6204 produced 3,219 synchronized simulator frames on MPS, including 2,559
  neural-policy frames and four contact-gated assist windows.
- Correction export split those windows into four contiguous episodes totaling
  660 frames: 121-272, 709-862, 1864-2074, and 3076-3218.
- Corrected joint means are in the accepted LeRobot frame; shoulder/elbow means
  are 96.844/-59.912 degrees versus base 104.740/-56.590 degrees.
- Exact red and blue per-frame tasks are present. No physical follower was opened
  or commanded.

## Verification

- 51 intervention/autolearn unit tests pass.
- The old bootstrap correction root is rejected for missing contract evidence.
- Corrected merge passes with 12 episodes, 11,316 frames, and pinned stats SHA-256
  `649c8cf43238217fabf9b226b0d292f2cc4ac06130cc619c7b182531c0c063d3`.
- Cycle dry-run and autonomous-workflow audit pass.

## Failed Verification Attempts

The first checker used the wrong task metadata filename, a test environment
without pytest/bpy, and nonexistent optional CLI flags. These were checker
assumption errors. Verification was rerun with `tasks.parquet`, direct unittest,
the supported dry-run interface, and the repo workflow audit.

## Proof Boundary

The canary's terminal 4/4 sort is controller-assisted simulation evidence, not
strict autonomous success. M10 proves training-data integrity, not competence.

## Next Step

T11.1 deterministic source- and phase-balanced replay with logged exposure.
