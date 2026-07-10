# SceneSmith PI0.5 recovery

## Outcome

PI0.5 now runs on Apple Silicon MPS inside the SceneSmith SO-101 workcell and
completes the four-cube red/blue sorting example. The accepted deployment is an
explicit hybrid: PI0.5 performs closed-loop visual search and grasp attempts;
contact-gated task-space primitives perform tray transfer and bounded recovery
after a neural search timeout. No cube pose is assigned or teleported.

Accepted private model:

- `jakekinchen/pi05-scenesmith-so101-sort-lora-v10-red-balanced-250`
- Hub revision: `770164688b8a913df8d0eb92e6984457117731a6`
- adapter SHA-256:
  `8c3ab23e261970c609dfafefa319231120266119e61b215011dc8814563af06e`

## Original failure

The original `pi05_smoke_physical_wrist_mps_1step` artifact was a dependency
smoke test, not a sorting policy:

- one optimizer step inside a 1,000-step warmup;
- repeated 64x64 still images instead of fresh observations;
- cube motion independent of robot actions;
- wrong camera, calibration, state-width, and aspect-ratio semantics;
- 50 queued actions consumed before observation feedback.

The public `Cache-SCA/pi05_teleop_sort_block` checkpoint loads on MPS but does
not transfer zero-shot to this workcell.

## Data and training

The causal expert uses damped least-squares IK, MuJoCo contact physics, and a
grasp constraint that can activate only after robot/cube contact. The final
private datasets are:

- `jakekinchen/scenesmith-so101-sort-causal-tail-v2`, revision
  `85816dbd70cba6592ab2124377a9cce8b1b70b7d`, eight episodes and 10,656
  frames, with 32/32 contact-gated grasps and 32/32 correct placements;
- `jakekinchen/scenesmith-so101-sort-causal-tail-v2-stage-tasks`, revision
  `46e075a13588beaa18cbe8ca91cf06dbe800f159`, with separate red-pick,
  blue-pick, return-home, and general task labels.

V9 learned stage switching but retained a blue-side position bias. V10 resumed
from V9 checkpoint 125 for 250 steps at `5e-7`, sampling the 3,984 red-stage
frames at 4x weight. Training ran in bfloat16 on the retained A100 instance;
inference and accepted evaluation ran locally on MPS.

## Runtime contract

The local policy server now enforces:

- overhead `base_0_rgb`, wrist `left_wrist_0_rgb`, and intentionally empty
  `right_wrist_0_rgb` routing;
- synchronized 224x224 observations and six raw SO-101 state values;
- calibrated degree/MuJoCo conversion and the collision-checked home pose;
- a real 15-action horizon that clears PI0.5's internal 50-action queue and
  replans from the latest cameras;
- stage-specific prompts and deterministic seed search around the episode seed;
- MPS execution with PEFT and physical-follower reporting.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
external/leLab/.venv/bin/python scripts/robot_lab/local_policy_action_server.py \
  --host 127.0.0.1 --port 8833 \
  --policy-repo outputs/robot_lab/so101_desk_cube_sort/models/pi05-scenesmith-so101-sort-lora-v10-red-balanced-250 \
  --device mps --num-steps 10 --action-horizon 15 \
  --camera-map '{"observation.images.base_0_rgb":"overhead","observation.images.left_wrist_0_rgb":"wrist","observation.images.right_wrist_0_rgb":"empty"}' \
  --simulation-home '[0.050438,-1.697719,1.549157,1.059675,-0.053182,1.6]' \
  --body-joint-signs '[1,1,1,1,1]' \
  --body-joint-offsets-deg '[0,-105.85,89.58,0,0]'
```

## Hybrid control

`policy_gripper_tray_transfer` records each behavior separately:

1. PI0.5 receives the current overhead, wrist, state, and stage task.
2. A grasp is accepted only after physical robot/cube contact.
3. The transfer controller interpolates SO-101 joints through lift, carry, low
   matching-tray release, and return-home phases.
4. If a stage produces no valid grasp for 1,000 neural frames, deterministic
   seed search advances. A bounded pregrasp recovery may then approach one
   remaining cube, but its constraint still requires real contact.
5. Completed cubes are excluded from future assist activations.

The proof labels distinguish direct policy grasps, jaw-reflex recovery grasps,
neural action frames, controller frames, and human intervention frames. This is
not represented as a pure end-to-end neural policy.

## Accepted proof

Held-out seed 6204:

- 4/4 sorted, 0 misplaced, 0 outside;
- 3,219 synchronized observation frames;
- 2,559 neural action frames and 462 policy/contact frames;
- four contact-gated activations, including two bounded recovery activations;
- 341 tray-transfer, 109 recovery-pick, and 210 post-place controller frames;
- zero human intervention frames and no physical follower command;
- MPS, PEFT, real 15-step replanning, wrist, overhead, and side views verified.

Artifacts:

- `outputs/robot_lab/so101_desk_cube_sort/evals/v10-250-closedloop-hybrid-pregrasp-seed6204/randomized-episode-6204/intervention_episode_summary.json`
- `outputs/robot_lab/so101_desk_cube_sort/evals/v10-250-closedloop-hybrid-pregrasp-seed6204/randomized-episode-6204/intervention_trajectory.json`
- `outputs/robot_lab/so101_desk_cube_sort/browser-v10-plus-final.png`

The visible action server was restarted with V10-250, seed 6204, live PI0.5,
`policy_gripper_tray_transfer`, and no correction. A real plus-button click
completed and rendered `final 4/4, intervention 0 frames` in the in-app browser.

## Remaining operational note

The next learning step is now a checked-in, Git-guarded cycle rather than a
manual sequence. `configurations/robot_lab/pi05_autolearn.example.json` runs:

1. a pure-mode baseline on held-out seeds;
2. hybrid correction collection on disjoint training seeds;
3. six-axis DAgger correction export and aggregation with the causal base data;
4. a finite 25-step MPS fine-tune;
5. candidate evaluation on the same held-out seeds; and
6. promotion only when the candidate is complete, unassisted, above threshold,
   and non-regressing.

The known V10 trajectory re-exported 660 controller corrections and merged
cleanly with the 10,656-frame base dataset, producing a verified 11,316-frame
training set. This proves the data flywheel and schema path; it does not yet
prove that a trained candidate improves autonomous sorting.

The first real bootstrap then completed five MPS optimizer steps, finalized and
reloaded the candidate, and evaluated the same held-out seed as the baseline.
Both policies sorted 0/4 at the 200-frame bound, so the promotion gate rejected
the candidate and left V10 accepted. The next checked-in cycle expands to four
collection seeds, 25 steps, and four held-out seeds.

Cycle manifests and the accepted-checkpoint pointer live under
`experiments/pi05_autolearn/`. Generated datasets and weights stay under
ignored `outputs/`. The local example uses no paid external compute. The final
Brev inventory check on 2026-07-10 reported no workspaces.
