# Slice Brief 053 - Pinned Live Factories, Private Evidence, And Runtime Profile

**Date:** 2026-07-11

## Objective

Implement and verify, entirely offline, the final production interlocks between
the Brief 052 source-bound candidate and any future live static-pose bracket:
exact pinned Feetech/FFmpeg factories, immutable content-addressed private
success/failure evidence, and a machine-checked Codex hardware-supervised
runtime profile. Keep the live gate closed.

## Contract

- Define explicit `hardware-supervised` and `offline-autonomous` Codex profile
  fragments. The project default must be owner-interactive, and hardware
  execution must require `approval_policy=on-request`; `never` is valid only for
  the separate offline profile.
- Capture the requested Codex hardware profile through an exact `codex doctor`
  command and independently cross-check the latest persisted `turn_context` of
  the active `CODEX_THREAD_ID`. Bind the turn ID/context digest, Codex
  executable/version, effective approval and filesystem policies, project
  profile hashes, timestamp, and raw doctor-report digest into signed evidence.
  Reject synthetic, stale, cross-thread, non-on-request, malformed, re-signed,
  parent/child-policy-mismatched, or config-drifted hardware evidence.
- Build the production Feetech transport only from the code-pinned LeRobot
  source tree and the candidate's exact follower path/protocol and six static-
  contract servo identities. Wrap it behind the existing read-only audited
  backend and static-pose adapter; connect must use `handshake=false`, reads must
  be raw `Present_Position` with zero retries, and close must use
  `disable_torque=false`.
- Build each production camera only from the candidate's fresh resolved camera
  and exact static mode/frame count. Require the pinned FFmpeg executable,
  exact-name AVFoundation finite PNG backend, and the live camera evidence
  class. No shell, property write, continuous capture, or alternate executable
  is permitted.
- Build and independently verify fixed success and failure evidence schemas.
  Both must embed the exact candidate contract and runtime-profile evidence,
  preserve candidate-only/no-proof-label authority, and be written exactly once
  beneath a content-addressed private session directory using exclusive create.
  Existing files, symlinks, path escape, identity mismatch, contract/profile
  substitution, or success/failure class relabeling must reject.
- Add deterministic adversarial tests before implementation where practical,
  run them in both pinned robotics runtimes, then run the broad offline authority
  and twin regression gate.

## Evidence and authority

This slice may grant only local offline conformance capabilities for the pinned
factory specification, private evidence format, and hardware-profile validator.
It cannot grant a live candidate result, `static_pose_bracketed_observation`,
`policy_shadow_input_valid`, policy shadow, physical qualification/transfer,
motion, promotion, or training.

Do not run the hardware-profile capture command against a live-eligible path,
enumerate or open a serial port/camera, instantiate a production bus/capture
process, call Studio, reconnect, write, change torque, command motion, preprocess
or run a policy, run MuJoCo, train, or start paid compute. All factory execution
tests use injected constructors/subprocess fakes. The live gate and training lock
remain closed.
