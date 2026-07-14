# Slice Brief 120 - T18.5 Dataset-Mixture And Training-Input Freeze

**Date:** 2026-07-13

## Objective

Freeze deterministic, reference-only dataset-mixture and training-input
manifests from the verified T18.1 selection through T18.4 snapshots. This
establishes reproducible source composition, not an actual training dataset or
permission to train.

## Contract

- Bind the exact ordered T18.2 cycle, T18.3 actor-safe components, and T18.4
  snapshot state. The mixture must contain all and only the 192 cycle windows,
  with zero correction windows while no source-bound correction event exists.
- Preserve every window's source phase, control mode, horizon, frame/component
  identity sequence, and the five named source action variants. The actor
  schema remains exactly top RGB, wrist RGB, joint position, and joint velocity.
- The training-input manifest is reference-only: no images/actions/state bytes
  may be copied into a buffer or read by a model. It must state `training_lock`
  closed and `training_eligible` false.
- The local mixture composition may be immutable/frozen for reproducibility;
  that local fact must not claim `simulation_training_ready` or optimizer
  authority.

## Acceptance Criteria

- Both manifests rerun byte-identically and contain the same ordered 192 window
  IDs and composition counts. Source/hash/cycle drift, duplicate or absent
  windows, privilege leakage, action-variant collapse, correction-count drift,
  buffer materialization, and training authority escalation fail closed.

## Out Of Scope

No model load/inference, optimizer/training, dataset-buffer materialization,
correction collection, raw rewrite, hardware, physical motion, Brev, external
compute, or deletion.
