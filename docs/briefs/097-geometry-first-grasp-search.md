# Slice Brief 097 - Geometry-First Grasp Search

**Date:** 2026-07-13

## Objective

Run the first deterministic bounded grasp search through the corrected explicit-
pad contact adapter and fixed-wrist/object-yaw solver without tuning friction,
compliance, mass, or contact time constants.

## Contract

- Use a reproducible bounded low-discrepancy design over wrist flex, wrist roll,
  object yaw, lateral x/y and vertical pregrasp offsets, and close target.
- Derive and record every range from compiled joint limits, the simulation
  aperture audit, object dimensions, table clearance, and reachable workspace.
- Reject bad IK, requested-variable drift, initial self-contact, approach object
  motion, table contact, and non-pad robot/object contact before eligibility.
- Close slowly without weld, constraint assist, scripted object motion, or
  teleport; retain pad-qualified object-frame contacts and effort evidence.
- Require strict-v2 representative pad geometry during grasp confirmation and
  throughout the table-level hold for geometry eligibility.
- Rank geometry-eligible candidates lexicographically by valid duration, span
  margin, normal alignment, impact, object displacement, effort, and IK
  residual. Refine only around eligible candidates.
- Keep one deterministic geometry holdout excluded from selection and evaluate
  it only after candidate selection.

This slice may identify or reject geometry-eligible contacts. It may not claim a
full dynamic grasp, training readiness, physical calibration, or actuation.

## Verified Outcome

- Twelve deterministic seven-dimensional Halton training candidates and one
  untouched holdout were evaluated with fixed friction/compliance.
- Ten training candidates and the holdout passed pose setup; two training
  candidates rejected on fixed-wrist reachability.
- Zero explicit-pad contact frames and zero geometry-eligible candidates were
  observed. Five reachable training candidates contacted only preserved
  composite jaw geometry; five made no robot-object contact.
- The holdout also contacted composite non-pad geometry only and was excluded
  from selection.
- This mechanically isolates explicit fingertip-pad collision occlusion as the
  next causal correction. It does not justify friction tuning or range growth.
- Artifact identity: `bbba9eac27c335b4ea292f698f18277d9fbc17a1ce75c4678e85a8eeb33900ce`.
- File SHA-256: `143a3f83e7baa35e92f50f46cece3ada3c072023b521755408b68b62fcf62b05`.
- Twelve focused tests pass in each pinned runtime; the 178-test broad gate
  passes.
