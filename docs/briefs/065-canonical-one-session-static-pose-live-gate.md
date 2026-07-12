# Slice Brief 065 - Canonical One-Session Static-Pose Live Gate

**Date:** 2026-07-12

## Objective

Open exactly one finite T16.5c static-pose candidate gate from the canonical
single thread after Reviewer 090's rejected transition and remote preservation.

## Contract

- Effective window: `2026-07-12T17:45:00-05:00` through
  `2026-07-12T18:15:00-05:00`.
- Session limit: one; sessions started at transition: zero.
- Required runtime: thread `019f5372-6317-7112-a7bc-dd92914fa869`, turn
  `9395e4da-2d75-4063-9412-5da4ae2d2259`, `danger-full-access`,
  `on-request`, profile identity `80e4ce66d8687d4bc8631fdf2ccc2167ba87f329523a44a5f2067a2b0d006896`.
- The gate is effective only after its scoped commit is confirmed on
  `origin/codex/pi05-autolearn-loop`.
- Before device open: obtain a fresh short owner-presence lease; perform fresh
  USB, serial, and camera discovery; verify the exact follower, calibration,
  both signed serial aliases at zero deduplicated holders, both stable cameras
  and exact 640x480/30 modes, the complete candidate contract, and a new
  immutable private destination.
- Execute at most one candidate session and reclose on every outcome.

## Authority withheld

No configuration/register write, torque change, motion, handshake, retry,
model execution, policy actuation, training, paid compute, or T16.6 operation is
authorized.
