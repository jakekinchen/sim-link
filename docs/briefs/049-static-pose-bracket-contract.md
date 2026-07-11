# Slice Brief 049 - Static Pose Bracket Contract

**Date:** 2026-07-11

## Objective

Define and independently verify the offline production contract for a future
static-pose-bracketed physical observation. Bind the exact accepted T16.5b
camera identities/modes and signed CalibrationProfile, convert six ordered raw
position reads into declared policy-coordinate units, and fail closed unless a
finite camera batch is temporally enclosed by stable `q_before` and `q_after`
reads.

## Contract

- Bind CalibrationProfile `b360b4f6...`, accepted live manifest `eff3c824...`,
  six ordered joint/servo identities, and both signed camera identities/modes.
- Require exactly one raw `Present_Position` value per joint before and after
  the finite camera batch, with strict integer/raw-domain validation and no
  duplicate or missing identity.
- Independently apply the signed profile semantics: five body joints in degrees
  around calibrated range midpoint and the gripper in normalized percent with
  `0=closed`, `100=open`.
- Require the complete camera receive interval to follow the completed before
  read and precede the started after read; all monotonic timestamps must be
  strictly ordered and the total bracket duration must be finite and bounded.
- Require per-joint normalized drift at or below the exact signed tolerance:
  `0.5 degrees` for body joints and `0.5 percent` for the gripper.
- Bind exact operation counts and require twelve position reads, one construct/
  connect/no-torque-close lifecycle, two finite camera batches, zero retries,
  zero register/configuration writes, zero torque changes, zero motion commands,
  zero unexpected operations, and `physical_follower_commanded=false`.
- Produce deterministic fixture evidence and an offline verifier. Re-signed
  source, tolerance, time, coordinate, count, frame, or authority substitution
  must reject.

## Evidence and authority

The checked-in contract may grant only
`static_pose_bracket_contract_valid`. Fixture output may grant only
`fixture_static_pose_bracket_conformant`. Neither may grant
`static_pose_bracketed_observation`, `policy_shadow_input_valid`,
`policy_shadow`, physical qualification, transfer, motion, or training.

This slice must not enumerate or open hardware, instantiate a serial/camera
object, call Studio, reconnect the follower, preprocess policy inputs, run
inference or MuJoCo, write a register, change torque, move, train, or start paid
compute. The live gate and training lock remain closed.
