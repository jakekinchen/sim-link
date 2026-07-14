# Slice Brief 147 - T20.17 Source-Native Clean-Base Preflight

**Date:** 2026-07-14

## Objective

Create the persistent, source-bound LeRobot training dataset and mechanically
composed simulation-only authority required before the T20.17 clean
`lerobot/pi05_base` optimizer campaign.

## Contract

- Materialize one actual pinned `LeRobotDataset` from six immutable strict-v2
  T17.5b source episodes (seeds 0-5). Keep seeds 6-7 outside the dataset as the
  frozen held-out evaluation set.
- Preserve source images, canonical SO-101 joint order, and measured actions.
  Convert MuJoCo radians to the existing canonical LeRobot degree/percent
  representation through the verified coordinate bridge. Do not fabricate,
  pad, interpolate, or infer actions.
- Bind all six package episodes to their raw-rollout identities with the
  existing native manifest, and bind LeRobot's own train-dataset statistics.
  No parallel SceneSmith training store or independent normalization result may
  become the training source.
- Bind the complete local `lerobot/pi05_base` snapshot by repository, revision,
  file bytes, and model weight identity. Network access remains disabled and no
  second checkpoint fetch is allowed.
- Define a bounded future campaign: rank-4 LoRA, local MPS, batch size 1, 250
  optimizer updates, seed 20260714, LeRobot dataset statistics installed at
  processor initialization, and strict-v2 evaluation from held-out seed 6.
- Convert the owner's standing direction to enact the MVP plan into a signed,
  T20.17-specific simulation-only grant and central authority decision. The
  composer must grant only `simulation_training_ready`; it must deny physical
  transfer, promotion, hardware, external compute, and Brev.
- Do not load a model, run inference, execute an optimizer, or run a simulator
  rollout in this slice. Preserve unrelated dirty files and vendored checkouts.

## Acceptance Criteria

- The pinned LeRobot runtime creates and reopens a six-episode, 1,464-frame
  dataset with deterministic source annotations and no held-out episode.
- Dataset metadata/statistics, episode content, source raw bytes, base snapshot,
  campaign bounds, and held-out identity are signed and reverified.
- Tampering with a source episode, split, frame/action semantics, dataset
  metadata, base snapshot, campaign budget, owner grant, or central decision
  fails closed.
- Focused tests plus the relevant stack, coordinate, manifest, authority,
  documentation, and project-state gates pass.
- State, ledger, MVP plan, session log, reviewer decision, scoped commit, and
  remote branch agree before any optimizer execution.

## Out Of Scope

Optimizer execution; model load or inference; strict rollout execution;
T20.18-T20.22; hardware or camera access; Robo Scan; external compute; Brev;
physical transfer; promotion; dataset augmentation; recovery episodes; or
posterior calibration.
