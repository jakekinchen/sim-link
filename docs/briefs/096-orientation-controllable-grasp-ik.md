# Slice Brief 096 - Orientation-Controllable Grasp IK

**Date:** 2026-07-13

## Objective

Replace position-only grasp setup with a solver whose requested wrist flex,
wrist roll, and object yaw remain independently controllable and mechanically
verified before any contact simulation.

## Contract

- Fix candidate wrist flex and wrist roll values exactly; solve only shoulder
  pan, shoulder lift, and elbow flex for the requested pregrasp position.
- Preserve joint limits, regularize toward the current configuration, reject
  non-finite inputs/residuals, and report initial/final collision status.
- Record requested and achieved wrist flex/roll, position residual, complete
  achieved gripper rotation, approach axis, and pad-derived closing axis.
- Apply object yaw explicitly to its free-joint quaternion, run forward
  kinematics, read yaw back independently from the object body, and reject
  tolerance drift.
- Record requested and achieved pregrasp position, lateral x/y/vertical
  offsets, approach vector, closing axis, and object yaw for every candidate.
- Reject candidates before contact simulation when requested variables are not
  achieved within declared tolerances.

This slice may prove controllable pose setup. It may not claim a geometry
search, contact, grasp, training readiness, physical calibration, or actuation.

## Verified Outcome

- Four deterministic candidates independently span wrist flex -0.5 to 0.5
  rad, wrist roll -1.2 to 1.2 rad, and object yaw -0.6 to 0.6 rad.
- All four preserve exact requested wrist values and independently read back
  exact requested object yaw after forward kinematics.
- Maximum position residual is 0.000537937313 m against a 0.001 m limit.
- Requested/achieved positions, approach axes, closing axes, full achieved
  rotations, and lateral/vertical offsets are retained per candidate.
- All initial and solved states are free of forbidden non-adjacent robot
  self-contact. Out-of-range wrist requests and non-finite inputs fail closed.
- Artifact identity: `cdcb2359955dc590ba46e7f262835afd61106dfdc9b40844594f1190743ae51b`.
- File SHA-256: `9b6accc6d9288eff3d039c6ada6d6dc82037eeeff2ff8e8d7070c0da123a1c92`.
- Ten focused tests pass in each pinned runtime; the final 176-test broad gate
  passes.
