# Slice Brief 103 - Best Principal-Axis Wrist Solve

**Date:** 2026-07-13

## Objective

Evaluate both valid horizontal principal axes of the rectangular anchor and
select the best mechanically reachable wrist pose without relaxing Brief 102's
orientation gates.

## Contract

- Apply the identical bounded flex/roll solver independently to the settled
  anchor's object-frame x and y axes.
- Accept an axis only at absolute alignment of at least 0.95 and closing-axis
  absolute vertical component of at most 0.1; select the lower deterministic
  orientation error when both pass.
- Record the selected object axis and both-axis failure context.
- Preserve object yaw, offsets, close target, seed, holdout role, wrist bounds,
  settling, pad-midpoint targeting, trajectories, explicit-pad proxy, contact
  physics, evaluator, ranking, candidate count, and excluded holdout.

This slice may establish a horizontal principal-axis pose or strict contact
geometry. It may not claim a dynamic grasp, training readiness, physical
calibration, or actuation.

## Verified Outcome

Eight of twelve candidates satisfy the unchanged horizontal gate, all on the
anchor y axis; six also pass the approach-motion gate. Two candidates produce
bilateral explicit-pad contact through all eight hold frames. Candidate 3
reaches a 17.398 mm maximum representative span but remains below the strict
20 mm minimum, and the best observed normal alignment across the bilateral
candidates is only `0.056071945` against the strict 0.8 minimum. Both bilateral
candidates also exceed the 0.1 mm approach-motion limit. No strict-v2 frame or
geometry-eligible candidate exists.

Artifact `06bc0f4a...` verifies byte-for-byte. Twenty focused tests pass in both
configured MuJoCo runtimes and the 190-test broad gate passes. This establishes
bounded horizontal anchor-y pose feasibility and repeatable bilateral contact
only. Strict contact geometry, geometry eligibility, unassisted MuJoCo grasp,
training readiness, physical calibration, and actuation remain withheld.
