# Slice Brief 101 - Principal-Axis-Aligned Search

**Date:** 2026-07-13

## Objective

Replace independent wrist-roll sampling with a mechanically verified roll that
aligns the compiled pad closing axis to the settled anchor's object-frame x
principal axis.

## Contract

- For each existing candidate, keep its object yaw, wrist flex, offsets, close
  target, seed, and holdout role unchanged.
- Search a fixed deterministic roll grid within the existing wrist-roll range,
  solve the same pad-midpoint IK at the same pregrasp target, and select the
  reachable roll with maximum absolute closing-axis/object-x alignment.
- Record the original sampled roll, selected roll, requested object axis,
  achieved closing axis, and alignment; fail closed below the declared
  canonical strict-v2 0.8 alignment threshold.
- Preserve passive settling, approach/pregrasp/close/hold trajectories,
  explicit-pad proxy, friction, compliance, mass, contact time constants,
  evaluator, ranking, candidate count, and excluded holdout.

This slice may establish strict contact geometry or a geometry-eligible
simulated candidate. It may not claim a dynamic grasp, training readiness,
physical calibration, or actuation.

## Verified Outcome

The first run failed closed because a provisional 0.95 threshold exceeded the
canonical strict-v2 0.8 alignment requirement. After correcting the slice to
the canonical threshold, four candidates produced reachable compiled
closing-axis/object-x alignments from `0.805711283` to `0.885754769`; two also
passed the approach-motion gate. None reached the moving pad. The aligned axes
retained vertical components from `0.451419816` to `0.589696657` because wrist
flex remained fixed, leaving zero bilateral-contact, strict-v2, or
geometry-eligible candidates.

Artifact `34b2a47c...` verifies byte-for-byte. Sixteen focused tests pass in
both configured MuJoCo runtimes and the 186-test broad gate passes. This
establishes only deterministic compiled principal-axis wrist-roll alignment.
Bilateral contact, geometry eligibility, unassisted MuJoCo grasp, training
readiness, physical calibration, and actuation remain withheld.
