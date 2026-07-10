# Slice Brief 001 - domain randomized intervention loop

**Date:** 2026-07-09

## Objective

Replace the partial post-hoc intervention proof with a SceneSmith-owned control-step loop that randomizes valid workcells, arbitrates policy and leader actions under a deadman, records synchronized observations, exports correction data, and is operable from the action server.

## Product / Project Value

This turns the generated SO-101 room from a visual episode player into a repeatable evaluation and correction-data factory for PI0.5 or another LeRobot policy.

## Acceptance Criteria

- Randomization is deterministic, actually applied to MuJoCo, and collision-aware.
- The leader bridge imports no follower class and never opens the known follower port.
- Each recorded frame distinguishes policy proposal, human proposal, executed action, and intervention state.
- Camera observations are rendered at the recorded simulation state and differ over time.
- The LeRobot dataset reloads with aligned state/action/image features and correction sidecar data.
- Browser controls support batch size, seed, arming, press-and-hold takeover, and live status.
- Proof language labels scripted failure injection separately from real-contact manipulation and neural autonomy.

## Expected Files

- `scenesmith/robot_lab/domain_randomization.py`
- `scenesmith/robot_lab/leader_arm_bridge.py`
- `scenesmith/robot_lab/intervention_supervisor.py`
- `scripts/robot_lab/run_randomized_intervention_eval.py`
- `scripts/robot_lab/export_intervention_dataset.py`
- `scripts/robot_lab/robot_action_server.py`
- `scripts/robot_lab/verify_robot_action_server.mjs`
- `tests/unit/test_robot_lab_intervention.py`
- `docs/so101-domain-randomized-interventions.md`

## Test Plan

Use unit tests for deterministic mechanics and safety boundaries, a three-seed MuJoCo batch for episode proof, LeRobot reload for dataset proof, a read-only leader sample if the port is free, and Playwright verification for the action-server workflow.

## Validation Commands

Use the commands in `docs/autonomous-workflow/09-autonomous-milestones.md`.

## Evidence To Record

Store all generated proof under `outputs/robot_lab/so101_desk_cube_sort/intervention-proof`, `datasets/intervention-proof`, and `action-server-intervention-proof`.

## Reachability / Demo Proof

The user can open `http://127.0.0.1:8822/`, start a randomized batch, observe a detected failure, hold the takeover control, and inspect the resulting corrected episode and camera views.

## Cross-Doc Impact

Update `docs/so101-lelab-scenesmith-bridge.md` with the new ownership, safety, and dataset contracts.

## Out Of Scope

- Sending commands to the physical follower.
- Claiming a base PI0.5 checkpoint autonomously solves the full sort without task-specific training.
- Replacing LeRobot's dataset implementation.

## Stop Conditions

- Any path can write to a follower without an explicit separate hardware project boundary.
- Frame observations are not synchronized to the action/state row they label.
- Browser proof can only replay a fabricated result rather than invoke the real episode endpoint.
