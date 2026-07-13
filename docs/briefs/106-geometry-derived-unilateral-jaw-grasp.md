# Slice Brief 106 - Geometry-Derived Unilateral-Jaw Grasp

**Date:** 2026-07-13

## Objective

Replace stale Halton close/height/axis-offset guesses with a mechanically
derived unilateral-jaw grasp and verify a complete unassisted MuJoCo cycle.

## Contract

- Start from the verified candidate-3 object yaw and transverse orientation
  context, not its close target, vertical target, or selected-axis offset.
- Derive target aperture as the selected 35 mm anchor width plus two explicit
  pad normal half-thicknesses; invert the checked monotonic aperture curve by
  deterministic piecewise-linear interpolation to obtain gripper q.
- Set pad-midpoint vertical offset to object-center height and derive fixed-jaw
  approach clearance as two explicit pad normal half-thicknesses opposite the
  fixed-to-moving selected axis.
- Rerun the bounded best-axis wrist solve, then execute approach, pregrasp,
  close, 8-frame hold, 24-frame 40 mm lift, 12-frame unsupported hold,
  24-frame lower, release, release settle, and retreat with no assist.
- Use the unchanged strict-v2 contact evaluator on every grasp/transport frame,
  require the existing 0.1 mm preclose-motion gate, preserve the complete
  release/retreat contact transition, require source-clear final retreat, and
  require exact two-pass determinism.
- Preserve proxy geometry, friction, compliance, mass, contact time constants,
  evaluator thresholds, object yaw, transverse offset, seeds, and all hardware,
  training, and live gates.

The slice may establish a strict unassisted MuJoCo grasp. It may not grant
simulation training readiness, physical calibration, or physical actuation.

## Verified Outcome

- The 35 mm selected anchor width plus two 1 mm pad half-thicknesses yields a
  37 mm target aperture and a checked-curve inverse of 0.2492469645 rad.
- The object-center vertical target and -2 mm fixed-jaw clearance leave only
  5.985e-9 m of preclose object motion. The clearance is mechanically verified
  opposite the fixed-to-moving closing axis (dot 0.980329).
- Strict-v2 contact holds for 8/8 grasp-hold, 24/24 lift, 12/12 unsupported
  lift-hold, and 24/24 lower frames. Lift height is 36.271 mm, all 12 hold
  frames are support-free, and no assist or non-pad robot/object contact occurs.
- Opening alone retains fixed-pad contact; the complete transition is preserved
  and the final retreat frame is contact-clear. The proof does not claim every
  release/retreat frame is clear.
- Artifact identity `30c5873ae8922ce5238c6bc1aea38bb4e6b6fafd937f25932e93f1128d39e51d`;
  file SHA-256 `d0b847e68e708e8de2ded6620b8a9c6e96c88264ec256989b83eb7b829db46b7`.
- Four focused tests pass in both configured runtimes, artifact verification
  and compilation pass, and the 198-test broad authority/twin/grasp gate passes.
