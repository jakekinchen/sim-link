# Slice Brief 092 - Contact Span And Friction Sweep

**Date:** 2026-07-13

## Objective

Derive nominal metric jaw-contact span directly from MuJoCo contact geometry and
test whether a bounded friction/contact-compliance sweep can retain the accepted
two-jaw grasp through an unassisted lift and hold.

## Contract

- Freeze the Brief 091 object, pose, wrist roll, pregrasp height, close target,
  trajectory, seed, and strict lift threshold.
- Measure fixed-to-moving-jaw span only from simultaneous MuJoCo contact points;
  do not infer physical aperture.
- Sweep only a finite declared grid of simulation friction and contact time
  constants. Keep object mass and geometry fixed.
- Select on a training grid using maintained unassisted lift clearance,
  two-jaw lift-hold contact, bounded impact, and deterministic replay.
- Reserve one parameter combination as an untouched holdout until selection is
  complete.
- Use no weld, equality assist, teleport, scripted object motion, policy, or
  physical hardware.

This slice may establish a simulation-only contact-span profile and a candidate
contact model. It may not establish physical gripper calibration, qualified
twin dynamics, strict policy success, training readiness, or motion authority.

## Verified Outcome

- Nineteen simultaneous-jaw baseline frames produce a MuJoCo contact-point span
  from 0.03286691 m during closure down to 0.004907838 m during hold.
- The collapsing span shows that two named jaw bodies converge on one local
  object region; contact count alone does not establish opposing force closure.
- None of 12 training-grid friction/time-constant settings maintains lift or any
  two-jaw lift-hold frame. No training candidate is selected.
- The untouched friction 4.0 / time constant 0.01 s holdout also fails, ending
  at object z 0.322867 m with zero lift-hold two-jaw frames.
- Artifact identity: `89c0406265f406002c1e0e2c61297f89a1e1db5962fa0b3c7ee1fed15f32a3ba`.
- File SHA-256: `8860549b501029f8b8dbe0661bbd43855dffe12e60e68fd6454358c2ead8366b`.
