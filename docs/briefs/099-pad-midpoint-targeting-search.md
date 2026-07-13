# Slice Brief 099 - Pad-Midpoint Targeting Search

**Date:** 2026-07-13

## Objective

Correct the object-target convention proven wrong by Brief 098 and rerun the
identical bounded search.

## Contract

- For each wrist pose and close target, solve the shoulder/elbow configuration
  so the predicted midpoint between fixed and moving pad references—not the
  fixed-adjacent gripperframe—matches the requested object-relative target.
- Verify the achieved predicted midpoint after forward kinematics and reject
  excess residual before approach.
- Keep the 12 Halton candidates, untouched holdout, wrist/yaw/offset/close
  ranges, trajectory frame counts, explicit-pad proxy model, friction,
  compliance, mass, contact time constants, evaluator, and ranking unchanged.
- Enforce preclose object-motion and non-pad-contact rejection in addition to
  bilateral pad-qualified strict-v2 hold geometry.

This slice may establish bilateral pad contact or a geometry-eligible hold. It
may not claim a full dynamic grasp, training readiness, physical calibration,
or actuation.

## Verified Outcome

The identical 12-candidate search plus excluded holdout produced two
simulation candidates with bilateral explicit-pad contact through all eight
hold frames. Candidate 1 produced three bilateral close frames with
representative spans of 5.796-7.695 mm and best inward-normal alignment
`-0.279906875`; candidate 3 produced five bilateral close frames with spans of
8.167-14.425 mm and best alignment `-0.053688997`. Neither produced a strict-v2
valid hold frame. Their preclose object displacements were 8.474 mm and
2.101 mm respectively, so both also fail the approach-motion gate.

Artifact `d18db60c...` verifies byte-for-byte. Twelve focused tests pass across
the two configured MuJoCo runtimes, and the 182-test broad gate passes. This
establishes `bilateral_explicit_pad_contact_observed` only. Geometry-eligible
grasp, unassisted MuJoCo grasp, training readiness, physical calibration, and
actuation remain withheld.
