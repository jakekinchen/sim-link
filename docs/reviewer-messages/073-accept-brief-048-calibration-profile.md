# Reviewer Decision 073 - Accept Brief 048 Calibration Profile

**Date:** 2026-07-11

## Decision

`CONTINUE T16.5C; ACCEPT BRIEF 048 SIGNED CALIBRATION PROFILE OFFLINE; LIVE GATE CLOSED`

## Evidence

Implementation `700be05468c15e3660bf481931f77e49af49d527` is present on
`origin/codex/pi05-autolearn-loop`. Tracked profile `b360b4f6...` independently
rebuilds from pinned calibration `192404b6...`, accepted live manifest
`eff3c824...`, and the exact six-servo identity digest `66e9d363...`.

The verifier rejects missing, extra, duplicate, or mismatched joints/IDs;
booleans and nonintegers; out-of-domain homing offsets and position ranges;
inverted ranges; nonzero drive mode; calibration or accepted-manifest
substitution; and re-signed normalization, gripper-polarity, extra-field, or
global-authority drift. The tracked profile contains no raw calibration/device
path or USB serial and explicitly records no hardware access, follower command,
policy run, motion authority, or training authority.

Six focused tests, independent artifact verification, compilation, diff checks,
and the established 238-test offline authority/twin gate pass. The failed Black
invocations are environment-only: system Python lacks Black and the locked
project environment cannot resolve Linux-only Drake on macOS ARM; neither
changed files nor weakened verification.

Grant only local `calibration_profile_semantically_valid`. Do not grant
`static_pose_bracketed_observation`, `policy_shadow_input_valid`, `policy_shadow`,
actuation, physical qualification, transfer readiness, promotion, or training.
T16.5c remains in progress and T16.6 remains pending. The next slice must start
with an offline static-pose-bracket/coordinate contract; it must not reopen
hardware or run policy preprocessing/inference until separately reviewed.
