# Slice Brief 100 - Post-Yaw Settle Baseline

**Date:** 2026-07-13

## Objective

Separate passive object-yaw/table relaxation from gripper-induced preclose
motion before interpreting the approach-motion gate.

## Contract

- After writing and independently reading back each requested object yaw, step
  the unchanged model for one fixed 0.25-second passive settle interval.
- Record displacement and yaw drift during that interval, then define the
  preclose anchor from the settled pose.
- Preserve the 12 Halton candidates, excluded holdout, object-relative target
  offsets, pad-midpoint solver, arm/gripper trajectories, explicit-pad proxy,
  friction, compliance, mass, contact time constants, evaluator, ranking,
  ranges, and seeds.
- Keep passive-settle displacement distinct from gripper-induced preclose
  displacement and require the existing 0.1 mm approach-motion limit only of
  the latter.

This slice may clarify the causal source of object motion or establish a
geometry-eligible simulated candidate. It may not claim a dynamic grasp,
training readiness, physical calibration, or actuation.

## Verified Outcome

The passive settle separated substantial yaw/table relaxation from later
gripper-induced motion. Six of twelve candidates now pass the existing 0.1 mm
approach-motion gate. The two bilateral-contact candidates improved from
8.474/2.101 mm preclose displacement to 0.704/0.461 mm, but both still fail
that gate. Their bilateral contact persists through all eight hold frames, yet
the best observed span is 14.713 mm and the best alignment is `-0.051511158`,
so neither reaches the strict 20 mm/0.8 geometry thresholds and neither
produces a strict-v2 valid frame.

Artifact `75e1ff2b...` verifies byte-for-byte. Fourteen focused tests pass in
both configured MuJoCo runtimes and the 184-test broad gate passes. This
establishes only that passive settle and approach motion are causally separated
and that some candidates pass the approach-motion gate. Geometry eligibility,
unassisted MuJoCo grasp, training readiness, physical calibration, and
actuation remain withheld.
