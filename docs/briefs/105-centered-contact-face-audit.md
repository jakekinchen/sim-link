# Slice Brief 105 - Centered Contact-Face Audit

**Date:** 2026-07-13

## Objective

Diagnose the remaining normal-alignment failure from actual centered bilateral
contact evidence before changing pose, geometry, or physics.

## Contract

- Rerun only centered candidates 2 and 3 with identical inputs and simulation.
- Retain each bilateral close/hold aggregate's representative object-frame
  contact centroid, inward normal, span vector, alignments, force balance, and
  phase index.
- Classify each representative centroid against the nearest analytic anchor box
  face and record face residual without relabeling MuJoCo normals.
- Bind the existing geom-order-reversal convention proof and the source
  centered-search identity.
- Do not alter pose, target, contact geometry, friction, compliance, mass,
  evaluator, thresholds, trajectories, or authority.

This slice is diagnostic only and may not claim geometry eligibility, dynamic
grasp, training readiness, physical calibration, or actuation.

## Verified Outcome

Source-identical replay retained 15 bilateral close/hold aggregates for each of
candidates 2 and 3. The fixed-pad representative is classified on the anchor
`+z` top face in all 30 aggregates and carries inward normal `[0, 0, -1]`.
The moving-pad representative is on the `-y` side face in 27 aggregates and on
`+z` in three; its dominant inward normal is `[0, 1, 0]`. The existing
synthetic convention proof remains aggregate-valid and geom-order independent.
The normal-alignment failure is therefore a real top-face/side-face trajectory
condition, not a normal-sign or geom-order defect.

Artifact `23572851...` verifies byte-for-byte. Twenty-four focused tests pass
in both configured MuJoCo runtimes and the 194-test broad gate passes. This
establishes only the contact-face diagnosis. Geometry eligibility, unassisted
MuJoCo grasp, training readiness, physical calibration, and actuation remain
withheld.
