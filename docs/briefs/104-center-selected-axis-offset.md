# Slice Brief 104 - Center Selected-Axis Offset

**Date:** 2026-07-13

## Objective

Center the pad midpoint on the anchor along the selected principal/closing axis
while retaining the candidate's transverse and vertical target offsets.

## Contract

- Run the verified best-axis selection at the unchanged target, then project
  the candidate's horizontal target offset onto the selected object axis.
- Remove only that scalar projection, retain the orthogonal horizontal and
  vertical components, and rerun the bounded wrist solve on the same selected
  axis at the centered target.
- Record original, removed, and retained offset components plus the final
  achieved orientation evidence.
- Preserve object yaw, close target, seed, holdout role, wrist bounds,
  settling, trajectories, explicit-pad proxy, contact physics, evaluator,
  ranking, candidate count, and excluded holdout.

This slice may establish strict contact geometry or a geometry-eligible
simulated candidate. It may not claim a dynamic grasp, training readiness,
physical calibration, or actuation.

## Verified Outcome

Eight candidates remain horizontally feasible after selected-axis centering;
six pass the approach-motion gate. Two candidates retain bilateral contact
through all eight hold frames. Candidate 3 now reaches a 20.965 mm maximum
representative span, exceeding the strict 20 mm threshold, while candidate 2
reaches 19.915 mm. Contact-normal alignment remains failing at a best observed
`0.051848674` against the strict 0.8 minimum, and both bilateral candidates
still exceed the 0.1 mm motion limit. No strict-v2 frame or geometry-eligible
candidate exists.

Artifact `7deb2826...` verifies byte-for-byte. Twenty-two focused tests pass in
both configured MuJoCo runtimes and the 192-test broad gate passes. This
establishes selected-axis centering as a span correction only. Strict contact
geometry, geometry eligibility, unassisted MuJoCo grasp, training readiness,
physical calibration, and actuation remain withheld.
