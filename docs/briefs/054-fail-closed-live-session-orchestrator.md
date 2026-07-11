# Slice Brief 054 - Fail-Closed Live Candidate Session Orchestrator

**Date:** 2026-07-11

## Objective

Implement and verify, entirely offline, the single production orchestration path
that composes the Brief 053 full-contract/profile-gated factories, Brief 052 live
candidate runner, and immutable private success/failure evidence. Once trusted
preflight completes, the caller must receive a candidate result only after
exactly one private artifact is durably written and independently reverified.

## Contract

- Reverify the active same-thread hardware profile and complete candidate
  contract before starting a session or exposing a production constructor.
- Reject a missing, aliased, or previously consumed private-evidence destination
  during preflight, while retaining exclusive creation as the final race-safe
  write boundary.
- Build only the exact Brief 053 one-shot Feetech and two-camera factories and
  pass them to the fixed production live-candidate runner.
- Define the session start boundary after all non-hardware preflight succeeds.
  Preflight rejection writes no session artifact and cannot consume or open a
  hardware factory.
- On candidate success, build and verify fixed private-success evidence, write
  it once beneath the content-addressed session directory, independently verify
  the returned reference, then and only then return the candidate result.
- On candidate or cleanup failure after session start, build and verify fixed
  private-failure evidence, write and reverify it exactly once, then raise a
  typed rejection carrying only that rejected evidence/reference. Do not return
  a candidate result or proof label.
- If evidence construction, write, or reference verification fails, preserve
  both the primary and evidence error when both exist, make no second write
  attempt, and fail closed without a success return.
- If outcome timestamp acquisition fails or regresses after session start,
  preserve that failure (and the candidate failure when both exist), use the
  trusted start time only for the rejection record, and never return a result.
- Bind the result, hardware-profile identity, private-evidence identity, and
  private-reference hash into a candidate-only session receipt. The receipt
  grants no physical proof label or global authority.
- Add adversarial tests for preflight rejection, success, primary failure,
  cleanup/error groups, evidence-build failure, writer failure, reference drift,
  double-write attempts, result/profile substitution, and exception suppression.

## Evidence and authority

Fixture execution may grant only
`fail_closed_static_pose_live_session_orchestrator_conformant`. It cannot grant a
live candidate result, `static_pose_bracketed_observation`,
`policy_shadow_input_valid`, policy shadow, physical qualification/transfer,
motion, promotion, or training.

Do not capture an active hardware profile, enumerate or open serial/camera
devices, instantiate the production bus/camera factories, call Studio,
reconnect, write, change torque, command motion, preprocess or run a policy, run
MuJoCo, train, or start paid compute. Patch every production constructor and
runner in tests. The live gate and training lock remain closed.
