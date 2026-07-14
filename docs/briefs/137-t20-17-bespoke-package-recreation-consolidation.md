# Slice Brief 137 - T20.17 Bespoke/Package Recreation Consolidation

**Date:** 2026-07-14

## Objective

Make the T20.17 clean-base PI0.5 campaign smaller and more truthful. Preserve
the project-specific proof and grasp logic, eliminate unreferenced test-only
code, and establish the boundary for one signed manifest around one
`LeRobotDataset` and hashes from LeRobot's actual processor pipeline.

## Contract

- Keep `artifact_contract.py`, strict-grasp/contact semantics, geometry-derived
  grasp/episode generation, `so101_processor.py`, and the central
  authority/stack identity layer as bespoke, fail-closed components.
- Do not alter historical raw rollouts, signed evidence, outputs, checkpoint
  bytes, or the pinned `external/lerobot` checkout.
- Remove a listed module only after repository-wide import/reference inspection
  proves it has no production consumer. Preserve the lesson in the recreation
  map rather than retaining inert code.
- The replacement dataset boundary must be a thin signed manifest over a single
  `LeRobotDataset`: episode hashes, eligibility flags, quarantine reasons,
  task split, exact LeRobot metadata/stat hashes, and no translated training
  Parquet/window format.
- The replacement preprocessing boundary must run the pinned LeRobot pipeline
  and hash its actual finite outputs. It must not independently reproduce the
  pipeline merely to obtain a hash.

## Acceptance Criteria

- The checked-in map distinguishes retained IP, package-owned behavior, and
  retired surfaces with current call-site evidence and migration order.
- The first retirement removes only the three unreferenced test-only modules
  named by the audit and their dedicated tests; canonical SO-101 processor
  coverage remains.
- Focused regression and import discovery prove the retained package boundary
  still uses the pinned LeRobot stack and that no deleted module is referenced.
- No optimizer, model inference, simulator rollout, hardware, external compute,
  or Brev work occurs in this first consolidation slice.

## Out Of Scope

Training execution, current-evidence rewriting, physical-twin/live-observation
replacement, deletion of the historical T19.0 artifacts, physical access,
external compute, and Brev.
