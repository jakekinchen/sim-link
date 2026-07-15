# Slice Brief 171 - T20.35e Top-Two-Channel Classification Correction

**Date:** 2026-07-15

**State:** `verified`

## Objective

Correct T20.35d's under-specific residual classification by adding a
deterministic top-two-channel concentration test without changing its immutable
decoded or residual evidence.

## Contract

- Bind signed T20.35d report `13b08e70...` and preserve its five decoded
  chunks, target/residual matrices, 366 threshold coordinates, per-joint and
  boundary counts, original classification, and original route unchanged.
- Sort joint exceedance counts deterministically by descending count then joint
  index. Compute top-one and top-two fractions from the exact 366-coordinate
  population.
- Declare multi-channel concentration only when the top two joints together
  hold at least 75% of all threshold exceedances. Keep single-joint (50%) and
  chunk-boundary (60%) classifications distinct.
- Route a multi-channel result to a separately reviewed normalized-space
  residual and target-saturation audit for the selected channels before any
  decoder, projection, normalization, threshold, or training change.
- Run no model, inference, optimizer, checkpoint read/mutation, dataset write,
  rollout, hardware, external compute, or Brev.

## Acceptance Criteria

- Deterministic tests reject source identity, coordinate/count, sorting,
  fraction, threshold, classification, route, non-finite, and forbidden-action
  drift.
- One signed correction distinguishes the immutable T20.35d predeclared label
  from the derived top-two-channel semantic without rewriting history.
- Focused and relevant broad tests, same-agent review, canonical state, ledger,
  session log, reviewer decision, scoped commits, and remote preservation
  agree.

## Out Of Scope

Model construction; inference; optimizer; training; checkpoint or report
mutation; normalized-space attribution itself; action or threshold correction;
Gate C; rollout; hardware; external compute; Brev; transfer; or promotion.

## Result

Correction `f2a8aa8089467b019310d24152f417d7987de0880d9664f3ef1184818a2ddea3`
preserves immutable report `13b08e70...` and deterministically ranks wrist
roll (164 exceedances) then gripper (121). Their 285/366 combined exceedances
are 77.87%, above the predeclared 75% top-two threshold, while neither the 50%
single-joint threshold nor the 60% boundary threshold passes. The corrected
classification is `multi_joint_output_channel_concentrated`, routing only to a
model-free normalized-space residual and target-saturation audit. No model,
inference, optimizer, checkpoint access, action correction, or Gate C work
occurred.
