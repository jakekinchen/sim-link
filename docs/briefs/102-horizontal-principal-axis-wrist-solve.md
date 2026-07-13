# Slice Brief 102 - Horizontal Principal-Axis Wrist Solve

**Date:** 2026-07-13

## Objective

Jointly solve wrist flex and roll within their existing ranges so the compiled
pad closing axis is horizontal and aligned to the settled anchor x axis.

## Contract

- Preserve each candidate's object yaw, offsets, close target, seed, and
  holdout role while replacing its independent wrist flex and roll with one
  bounded deterministic two-dimensional orientation solve.
- Evaluate a fixed coarse grid plus three deterministic local refinements and
  fail closed unless absolute object-x alignment is at least 0.95 and the
  closing-axis absolute vertical component is at most 0.1.
- Preserve post-yaw settling, pad-midpoint targeting, trajectories,
  explicit-pad proxy, friction, compliance, mass, contact time constants,
  evaluator, ranking, candidate count, and excluded holdout.

This slice may establish a horizontal principal-axis pose or strict contact
geometry. It may not claim a dynamic grasp, training readiness, physical
calibration, or actuation.

## Verified Outcome

No candidate met both declared orientation conditions within the existing
wrist bounds. The closest tradeoffs included 0.840715959 alignment with
0.151806001 vertical component and 0.816468489 alignment with 0.178690132
vertical component. Because the orientation gate failed closed, no candidate
advanced to contact execution; bilateral, strict-v2, and geometry-eligible
counts are all zero.

Artifact `fd04d757...` verifies byte-for-byte. Eighteen focused tests pass in
both configured MuJoCo runtimes and the 188-test broad gate passes. This is a
bounded negative kinematic result only. Horizontal-axis feasibility,
bilateral contact, geometry eligibility, unassisted MuJoCo grasp, training
readiness, physical calibration, and actuation remain withheld.
