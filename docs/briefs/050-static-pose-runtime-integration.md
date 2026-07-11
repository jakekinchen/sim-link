# Slice Brief 050 - Static Pose Runtime Integration

**Date:** 2026-07-11

## Objective

Integrate the verified Brief 049 contract into a bounded production runtime
orchestrator using only injected fake transports and finite cameras. Prove the
exact lifecycle and cleanup required before a future live-gate review without
enumerating or opening real hardware.

## Contract

- Independently verify the tracked static-pose contract and all source bindings
  before constructing a transport.
- Require signed zero-holder snapshots across the complete canonical/alias
  identity before connect and after close, with stable path/existence evidence.
- Execute exactly: construct; connect with no handshake; six ordered
  `Present_Position` reads; two finite two-frame camera batches while the bus
  remains connected; six ordered position reads; close with
  `disable_torque=false`; post-close zero-holder verification.
- Bind strict monotonic intervals so the complete camera batch is enclosed by
  completed `q_before` and started `q_after` reads.
- Preserve primary, camera-release, transport-close, and post-close-holder
  failures without skipping cleanup or hiding an earlier error.
- Audit exact operation counts and reject any retry, register/configuration
  write, torque change, motion command, unexpected operation, residual
  connection, camera lifecycle drift, or follower command.
- Feed the resulting deterministic fixture observation through the Brief 049
  evaluator and emit signed runtime evidence bound to holder, transport,
  camera, observation, and result identities.

## Evidence and authority

The runtime result may grant only
`fixture_static_pose_bracket_runtime_conformant`. It must explicitly withhold
live bracket, synchronization/policy-input validity, shadow, physical
qualification/transfer, motion, promotion, and training authority.

This slice uses injected fake buses, cameras, holder snapshots, and clocks only.
It must not discover or open a serial port/camera, instantiate a live LeRobot
bus, call Studio, reconnect, write, change torque, command motion, preprocess or
run a policy, run MuJoCo, train, or start paid compute. The live gate and
training lock remain closed.
