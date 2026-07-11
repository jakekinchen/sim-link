# Slice Brief 052 - Source-Bound Static-Pose Live Candidate

**Date:** 2026-07-11

## Objective

Implement and verify, entirely offline, the production contract and bounded
runner that a later separately reviewed live gate would use for one static-pose-
bracket candidate. Resolve fresh numeric camera indexes from the Brief 051
stable identities, bind the exact follower USB/alias identity, active operator-
presence lease, project-state gate snapshot, calibration/static-pose sources,
and no-write lifecycle without opening hardware in this slice.

## Contract

- Accept only signed discovery v2 and an active, signed owner-presence lease for
  one session under an explicitly open, unconsumed, unexpired live-gate state.
- Bind the complete project-state digest and the exact gate session limit,
  sessions-started count, validity window, review decision, and scope.
- Resolve the follower from fresh discovery and require its USB identity digest
  to equal the accepted manifest-v5 digest; preserve the complete canonical and
  observed-alias path set for pre-open and post-close holder checks.
- Resolve each target camera by stable name/unique-ID/model-ID/input-mode hash,
  not a stored numeric index. Require exactly one match for each ordered static-
  pose camera and exact signed input-mode equality; additional unrelated cameras
  may not substitute for either target.
- Bind manifest `5218c3bd...`, CalibrationProfile `24db6f24...`, static contract
  `7260be3e...`, the exact twelve-read/two-finite-batch operation counts, and a
  finite duration no longer than the presence lease or reviewed gate.
- Execute only through the narrow live-marked adapter and finite camera
  interfaces: zero holders; connect without handshake; six `Present_Position`
  reads; two finite camera batches; six reads; close with
  `disable_torque=false`; stable zero holders.
- Preserve primary, camera-release, close, and post-holder failures; reject any
  write, retry, torque change, motion, unexpected operation, residual connection,
  path drift, identity drift, clock regression, pose drift, or authority drift.
- Emit a signed candidate-only result with no physical proof label. A later
  reviewed live execution and acceptance boundary must independently decide
  whether physical bracket evidence earns any label.

## Evidence and authority

Offline fixture execution may grant only
`source_bound_static_pose_live_candidate_runtime_conformant`. Contract
validation may grant only `static_pose_live_candidate_contract_valid`. Neither
grants `static_pose_bracketed_observation`, `policy_shadow_input_valid`, policy
shadow, physical qualification/transfer, motion, promotion, or training.

This slice may read the ignored accepted discovery/private evidence to verify
source resolution but must not enumerate or open a serial port/camera,
instantiate a real bus/capture process, call Studio, reconnect, write, change
torque, command motion, preprocess or run a policy, run MuJoCo, train, or start
paid compute. The live gate and training lock remain closed.
