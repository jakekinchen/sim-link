# Slice Brief 017 - Complete Quaternion Semantic Coverage

**Date:** 2026-07-10

## Objective

Finish the quaternion portion of T16.3 by applying canonical/effective rotation
comparison to every structural category that can carry a quaternion. Do not
start inferred-inertia, contact/friction, unnamed-geom, measured-mass, hardware,
or training work in this slice.

## Acceptance Criteria

- Quaternion scale and sign equivalence applies to joint frames, cameras,
  named sites, arm collisions, and gripper collisions.
- A missing quaternion is interpreted as MuJoCo's effective identity rotation
  only for fields where that default is valid.
- Comparisons use a documented small numeric tolerance after unit/sign
  canonicalization; true rotational differences remain mismatches.
- The five currently false arm-collision quaternion deltas disappear from the
  generated artifact without hiding their real geometry/position differences.
- `site:gripperframe` remains a true mismatch because of its position delta,
  while its equivalent quaternion contributes no delta.
- Raw XML values remain in mismatch records and canonical compared values remain
  available as provenance.

## Tests And Verification

- Scale-equivalent and negative-sign-equivalent quaternions in every relevant
  category compare equal.
- Missing-versus-explicit identity compares equal where MuJoCo defaults apply.
- A deliberately different rotation remains mismatched.
- The checked-in artifact has no quaternion numeric delta for the five known
  arm-collision regression records.
- Focused tests, sequential CLI write/verify, and the broader robot-lab suite
  pass.

## Exit Condition

Reviewer accepts complete quaternion coverage and routes back to Brief 016 for
inertial unknowns and effective contact/friction truthfulness. T16.3 remains
open.
