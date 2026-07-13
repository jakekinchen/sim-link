# Slice Brief 090 - MuJoCo Anchor Grasp Attempt

**Date:** 2026-07-13

## Objective

Execute one deterministic nominal anchor-cousin grasp in the pinned SO-101
MuJoCo model and feed measured simulation state through the unchanged strict
grasp semantics.

## Contract

- Use the pinned midpoint-calibrated SO-101 MJCF and declared nominal anchor
  geometry/mass from Brief 089.
- Preserve the physical anchor profile as unmeasured and distinct.
- Record raw MuJoCo object and gripper positions, contact evidence, contact-gated
  assistance, controller ownership, phase transitions, and deterministic replay.
- Derive no physical current or metric gripper aperture from absent calibration.
- Treat contact-gated weld assistance as controller assistance, never pure
  policy or unassisted grasp success.
- Evaluate the compiled ordered trace through the strict evaluator. Preserve a
  rejection as useful evidence rather than weakening thresholds or inventing
  missing measurements.

This slice may prove a deterministic MuJoCo attempt and expose the next concrete
grasping-twin correction. It may not grant unassisted MuJoCo grasp success,
policy success, physical twin qualification, training readiness, or motion.

## Verified Outcome

- Two exact 371-frame replays produced artifact identity `32f14feba6c10e501082c0438ee4b0cd80ee530d4c143468b5af20f5ad29626e`.
- The legacy placement score passes after contact-gated weld assistance; this is
  not unassisted grasp success.
- The unchanged strict evaluator rejects the attempt for peak contact impact,
  missing calibrated current, missing metric gripper aperture, one rather than
  two fingertip-side contacts, invalid stable hold, and contact-retaining release.
- Maximum selected-trace contact force is 17.081659463 N against the 5 N gate;
  maximum anchor step displacement is 0.004194223 m.
- The checked artifact contains all 371 non-image raw frames, controller state,
  contacts, assist state, object/gripper positions, simulated effort, and the
  compiled ordered strict trace.
- Nine focused tests pass; the relevant 69-test broad gate passes. The Brief 089
  analytic fixture remains byte-identical.
