# Executor Session 012 - Balanced PI0.5 Replay

**Date:** 2026-07-10

## Slice

Complete T11.1 with deterministic source- and phase-balanced training exposure
and an audit of the samples actually requested by the data loader.

## Result

- Replay plans are content-addressed to the merged dataset contract, merge
  summary, and correction sidecar.
- A 25-update plan contains 13 trusted-base draws and 12 correction draws.
- Correction exposure is evenly divided among recovery-pick, tray-transfer, and
  post-place phases (four draws each in the 25-update plan).
- The training wrapper installs a finite sampler without modifying the external
  LeRobot package and records every requested sample with source and phase.
- The wrapper rejects dataset hash drift, out-of-range indices, missing loader
  installation, and incomplete realized-draw audits.

## Verification

- 53 intervention/autolearn tests pass.
- Cycle dry-run includes explicit plan and audit artifacts.
- Six-update MPS smoke completed and saved checkpoint 000006.
- Realized audit exactly matched the smoke plan: three base, three correction,
  with one recovery-pick, one tray-transfer, and one post-place sample.
- Autonomous-workflow audit passes.

## Failed Attempt

The first smoke replaced `torch.utils.data.DataLoader` with a function, which
broke Accelerate's loader type check before update 1. The hook was corrected to
a proper subclass and the same plan then completed all six updates.

## Proof Boundary

This proves controlled exposure and MPS trainability. Six updates are a sampler
smoke, not evidence that task competence improved and not a promotable model.

## Next Step

T11.2 bounded context export around correction windows.
