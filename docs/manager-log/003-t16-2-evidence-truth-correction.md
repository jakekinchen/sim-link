# Manager Intervention 003 - Remove Fabricated Twin Evidence

**Date:** 2026-07-10

## Decision

`CORRECT THEN CONTINUE`

## Evidence Anchors

- `100`: The initial example reported `sim_joint_limit_projection_error=0.012`
  with status `pass`, but no held-out trace artifact existed.
- `100`: The initial profile reported `nominal_bus_voltage=12.0` with origin
  `read`, although no servo census had run.
- `100`: The coordinate parameter conflated simulator radians with the policy's
  calibrated degrees-plus-gripper-percent representation.

## Correction

Commit `ae6fe04` makes all unevaluated metrics `not_run`, keeps the bus voltage
unknown until T19.1, distinguishes policy and simulator action representations,
and rejects impossible qualification states, not-run measured values, and
unknown parameters carrying invented values.

T16.2 remains verified after correction. T16.3 may proceed.
