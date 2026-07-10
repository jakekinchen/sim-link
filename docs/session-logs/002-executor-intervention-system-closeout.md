# Executor Session 002 - intervention system closeout

**Date:** 2026-07-09

## Slice

Complete M2 through M5: control-step arbitration, synchronized episode capture,
LeRobot export, persistent PI0.5 inference on MPS, Studio leader takeover, and
the browser-visible randomized intervention workflow.

## Files Changed

- `scenesmith/robot_lab/domain_randomization.py`
- `scenesmith/robot_lab/intervention_control.py`
- `scenesmith/robot_lab/intervention_supervisor.py`
- `scenesmith/robot_lab/leader_arm_bridge.py`
- `scenesmith/robot_lab/policy_action_source.py`
- `scripts/robot_lab/export_intervention_dataset.py`
- `scripts/robot_lab/local_policy_action_server.py`
- `scripts/robot_lab/probe_local_policy_action_server.py`
- `scripts/robot_lab/robot_action_server.py`
- `scripts/robot_lab/run_randomized_intervention_eval.py`
- `scripts/robot_lab/sample_leader_source.py`
- `scripts/robot_lab/verify_intervention_batch.py`
- `scripts/robot_lab/verify_neural_policy_smoke.py`
- `scripts/robot_lab/verify_robot_action_server.mjs`
- `docs/so101-domain-randomized-interventions.md`
- `docs/so101-lelab-scenesmith-bridge.md`

## Tests / Validation

- Python compilation passed for every new or changed intervention module and
  command-line entry point.
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_robot_lab_scene_builder tests.unit.test_robot_lab_intervention`
  passed all 15 tests.
- `scripts/audit_autonomous_workflow.sh` reported `workflow audit clean`.
- `verify_intervention_batch.py` passed all checks for seeds 4100, 4101, and
  4102: 60 synchronized frames, 180 distinct images, and 12 intervention frames
  per episode.
- Both the 180-frame all-actions dataset and the 12-frame intervention-only
  dataset exported, reloaded, and verified.
- The persistent local PI0.5 server passed three MPS action requests. Warm
  queued requests completed in 0.012 and 0.011 seconds.
- The neural contact-physics smoke passed its truthfulness checks and reported
  the expected `neural_policy_stalled` task failure.
- The final Playwright run passed a two-seed browser batch with three cameras,
  the wrist-camera visual, AprilTag, policy/source controls, 17 robot mesh
  objects, 398884 triangles, and no console errors.

## Reachability

The operator workflow is live at `http://127.0.0.1:8822/`. The action server
can launch scripted acceptance batches or call the persistent PI0.5 service at
`http://127.0.0.1:8833`, while browser deadman heartbeats and Studio leader
samples control the simulated SO-101 without opening the follower port.

## Evidence

- `outputs/robot_lab/so101_desk_cube_sort/intervention-proof/intervention_batch_verification.json`
- `outputs/robot_lab/so101_desk_cube_sort/datasets/intervention-proof/scenesmith_intervention_export_summary.json`
- `outputs/robot_lab/so101_desk_cube_sort/datasets/intervention-only-proof/scenesmith_intervention_export_summary.json`
- `outputs/robot_lab/so101_desk_cube_sort/intervention-proof/local-policy-server-probe.json`
- `outputs/robot_lab/so101_desk_cube_sort/intervention-proof/neural-policy-contact-smoke/neural_policy_smoke_verification.json`
- `outputs/robot_lab/so101_desk_cube_sort/intervention-proof/studio-leader-control-smoke/run/randomized-episode-4200/intervention_episode_summary.json`
- `outputs/robot_lab/so101_desk_cube_sort/action-server-intervention-proof-final/action-server-proof.json`
- `outputs/robot_lab/so101_desk_cube_sort/action-server-intervention-proof-final/action-server-after-episode.png`

## Step-9 Flags For Reviewer

- The deterministic scripted harness proves reset, failure, correction,
  recording, export, and browser plumbing. It is not physical-contact or neural
  policy training data.
- PI0.5 inference is real and runs on MPS, but the current one-step smoke
  checkpoint stalls in this task and does not autonomously sort cubes.
- Studio leader takeover changed the simulated SO-101 state under a fresh
  deadman. That smoke had zero robot-cube contacts because no operator moved the
  leader through a grasp, so physical contact success is deliberately false.
- The working tree contains unrelated pre-existing changes and generated
  artifacts; none were reverted or staged.

## Next Suggested Slice

Run operator-guided contact corrections with the leader arm, export only those
intervention frames, then fine-tune and evaluate a task-specific PI0.5 policy as
a separate data-collection/training goal.
