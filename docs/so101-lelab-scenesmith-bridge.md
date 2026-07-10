# SceneSmith SO-101 LeRobot/LeLab Bridge

This bridge makes SceneSmith the owner of the generated robot simulation scene.
It accepts a natural-language desk sorting description, creates a 3D robot-lab
scene, exports a MuJoCo digital-twin backend, writes an inspectable Three.js
viewer, and emits LeRobot/LeLab-facing policy contracts.

## Generated Outputs

Default command:

```bash
./.venv/bin/python scripts/robot_lab/generate_so101_desk_sort.py
```

Default output directory:

```text
outputs/robot_lab/so101_desk_cube_sort
```

Key artifacts:

- `scene.json`: SceneSmith robot-lab structured scene contract.
- `scene_state.json`: object metadata for robot task binding and eval.
- `mujoco/scene.xml`: generated room, desk, trays, free cube bodies, cameras, and task sites around the included SO-101 model.
- `mujoco/so101_new_calib.xml`: copied TheRobotStudio SO-101 MuJoCo model with the base pose patched onto the generated desk.
- `mujoco/assets/*.stl`: copied SO-101 STL meshes used by MuJoCo.
- `viewer/index.html`: Three.js inspectable 3D scene that loads LeLab's SO-101 URDF/STL bundle.
- `viewer/so-101-urdf`: copied LeLab SO-101 URDF/STL bundle.
- `sim_bridge_contract.json`: digital-twin contract for robot state, action space, bodies, sites, cameras, and policy task.
- `lerobot/policy_request.json`: MolmoAct2/LeRobot-style action request.
- `lerobot/policy_request.rendered.json`: optional request populated with verifier-rendered images.
- `lerobot/lelab_manifest.json`: LeLab-facing import manifest.
- `proof_summary.json`: generation and oracle scoring proof.

## SO-101 Asset Source

The robot is no longer a SceneSmith proxy arm. The generated MuJoCo scene
includes `so101_new_calib.xml` from TheRobotStudio's SO-ARM100 simulation
assets. The generated browser viewer loads LeLab's bundled
`so101_new_calib.urdf` and corresponding STL meshes.

The real LeRobot motor/action order exported by SceneSmith is:

```text
shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
```

The LeLab/URDF joint-name order is:

```text
Rotation, Pitch, Elbow, Wrist_Pitch, Wrist_Roll, Jaw
```

LeLab applies additional URDF display corrections for `shoulder_lift` and
`elbow_flex`; SceneSmith records both naming schemes in
`sim_bridge_contract.json`, `scene_state.json`, `policy_request.json`, and
`lelab_manifest.json`.

## Camera Contract

The generated MuJoCo workcell now has three policy-observation cameras:

```text
cam0_side      fixed side/base view
cam1_overhead  fixed overhead view
cam2_wrist     wrist-mounted camera attached to the moving gripper body
```

`cam2_wrist` is inserted into the copied SO-101 MJCF as a visible
`wrist_camera` child body under body `gripper`. The assembly includes
`wrist_camera_body`, `wrist_camera_mount`, `wrist_camera_mount_foot`, and
`wrist_camera_lens` geoms, plus a matching `wrist_camera_anchor` site. The
browser viewer/action server also attaches a matching camera body to the URDF
`gripper` link, so the visible model and MuJoCo optical view use the same local
mount transform. The PI05 image slots are mapped as:

```text
observation.images.base_0_rgb        <- cam0_side
observation.images.left_wrist_0_rgb  <- cam2_wrist
observation.images.right_wrist_0_rgb <- cam1_overhead
```

The legacy MolmoAct2-style `cam0` and `cam1` placeholders remain in
`policy_request.json` for compatibility, but the simulation contract explicitly
advertises `cam0_side`, `cam1_overhead`, and `cam2_wrist`.

## Fiducial Contract

The scene now includes one valid AprilTag fiducial:

```text
apriltag_0  family tag36h11, id 0, fixed on the desk top
```

The tag is exported as first-class scene metadata in `scene.json`,
`scene_state.json`, `sim_bridge_contract.json`, `policy_request.json`, and
`lelab_manifest.json`. MuJoCo and the browser viewer render it as black/white
marker geometry rather than relying on texture-file support. It uses the
canonical 10x10 `tag36h11` ID 0 encoding. An independent detector decodes the
overhead render with Hamming 0; the tag remains outside the cube/tray
interaction path.

The calibration report is written to:

```text
outputs/robot_lab/so101_desk_cube_sort/fiducials/apriltag_calibration_report.json
```

Policy success does not depend on tag detection. The tag is a future
camera/world reconstruction anchor.

## Domain-Randomized Intervention Loop

The intervention implementation is tracked in:

```text
docs/robot_lab_domain_randomized_intervention_tasklist.md
```

The runtime path is SceneSmith-owned:

1. Randomize a bounded scene variant from a numeric seed.
2. Export the randomized SceneSmith/MuJoCo workcell.
3. Run the policy/controller episode.
4. Detect failure or accept forced-failure proof mode.
5. Apply a correction source to the simulated robot.
6. Record policy action, human/correction action, intervention flag, seed, and
   failure reason.
7. Export PI05-compatible LeRobot data plus a SceneSmith sidecar.

Correction sources:

```text
simulated_leader  deterministic proof source, no hardware required
physical_leader   read-only SO-101 leader arm, no physical follower commands
```

The physical follower remains disabled in this path. The browser proof verifies
`physical_follower_commanded=false`.

## LeRobot/LeLab Boundary

LeLab is the browser workflow shell for LeRobot calibration, teleoperation,
recording, training, replay, and inference. The generated `lelab_manifest.json`
is the adapter boundary: it points LeLab/LeRobot code at SceneSmith's generated
sim scene and policy request.

Set up the local LeLab environment from the cloned upstream project:

```bash
cd external/leLab
uv sync --python 3.12 --extra test
uv run lelab --help
```

Verify LeRobot exposes the correct SO-101 registry selectors:

```bash
cd external/leLab
uv run lerobot-teleoperate --help | rg 'so101_follower|so101_leader'
```

Use these registry type strings in commands and adapter configs:

```text
--robot.type=so101_follower
--teleop.type=so101_leader
```

Do not infer the robot type from direct `SO101FollowerConfig(...)` alias
construction alone. In LeRobot v0.6.x the same SO arm config class is registered
under both `so100_*` and `so101_*`; the CLI/config registry selector is the
authoritative type boundary.

When a compatible MolmoAct2 action server is available, pass it during export:

```bash
MOLMOACT2_ACTION_SERVER_URL=http://127.0.0.1:8792/predict \
  ./.venv/bin/python scripts/robot_lab/generate_so101_desk_sort.py
```

Without an action server, the export still proves the scene, digital-twin
contract, viewer, and oracle scoring loop. The action-server status is written
to `lerobot/policy_action_server_status.json`.

## Verification

Run standard-library unit tests:

```bash
./.venv/bin/python tests/unit/test_robot_lab_scene_builder.py
```

Load and step the generated MuJoCo scene:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/check_mujoco_scene.py \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --output-json outputs/robot_lab/so101_desk_cube_sort/mujoco-check.json
```

The MuJoCo check must pass all of these conditions:

- six robot controls are present;
- real SO-101 joints and actuators are present:
  `shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`,
  `gripper`;
- four free cube joints are present;
- `gripperframe`, `wrist_camera_anchor`, side camera, workspace, and tray
  target sites are present;
- `cam0_side`, `cam1_overhead`, and `cam2_wrist` cameras are present.

Validate desk/workcell placement and settled physics:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/validate_workcell.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --output-json outputs/robot_lab/so101_desk_cube_sort/mujoco/workcell_validation.json
```

The workcell validator checks that the SO-101 base is desk-mounted, trays are
seated on the desktop, cubes spawn on the desktop, all objects are inside the
desk footprint and room bounds, cubes settle on desk contacts, and contact
penetration remains bounded.

Render the generated MuJoCo scene and assert real SO-101 mesh provenance:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/render_mujoco_scene.py \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --camera cam0_side \
  --width 640 \
  --height 400 \
  --output-png outputs/robot_lab/so101_desk_cube_sort/mujoco/render-cam0-side.png \
  --output-json outputs/robot_lab/so101_desk_cube_sort/mujoco/render-summary.json
```

The render proof requires upstream mesh names such as `base_so101_v2`,
`upper_arm_so101_v1`, `under_arm_so101_v1`,
`wrist_roll_follower_so101_v1`, and `moving_jaw_so101_v1`.

Render the overhead and wrist policy views:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/render_mujoco_scene.py \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --camera cam1_overhead \
  --width 640 \
  --height 400 \
  --output-png outputs/robot_lab/so101_desk_cube_sort/mujoco/render-cam1-overhead.png \
  --output-json outputs/robot_lab/so101_desk_cube_sort/mujoco/render-cam1-overhead.json
```

```bash
./.mujoco_venv/bin/python scripts/robot_lab/render_mujoco_scene.py \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --camera cam2_wrist \
  --width 640 \
  --height 400 \
  --output-png outputs/robot_lab/so101_desk_cube_sort/mujoco/render-cam2-wrist.png \
  --output-json outputs/robot_lab/so101_desk_cube_sort/mujoco/render-cam2-wrist.json
```

Serve the output directory and verify the Three.js viewer:

```bash
cd outputs/robot_lab/so101_desk_cube_sort
python3 -m http.server 8811
```

```bash
node scripts/robot_lab/verify_threejs_viewer.mjs \
  --url http://127.0.0.1:8811/viewer/ \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/viewer-proof \
  --policy-request outputs/robot_lab/so101_desk_cube_sort/lerobot/policy_request.json \
  --output-policy-request outputs/robot_lab/so101_desk_cube_sort/lerobot/policy_request.rendered.json
```

The viewer verifier does not pass on a meshless URDF skeleton. It requires the
SO-101 URDF joint set and a nontrivial mesh load. The current verified output
loads 17 URDF mesh objects and 398,884 triangles, and writes:

- `viewer-proof/viewer-desktop.png`
- `viewer-proof/viewer-mobile.png`
- `viewer-proof/viewer-robot-closeup.png`
- `viewer-proof/viewer-proof.json`

Run the local scripted sorting policy baseline:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/run_sort_policy.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/policy_run
```

This writes:

- `policy_run/policy_run_summary.json`
- `policy_run/policy_trajectory.json`
- `policy_run/policy_final_side.png`
- `policy_run/policy_final_overhead.png`
- `policy_run/policy_final_wrist.png`

The current policy run sorts all 4 cubes into matching trays. This is a
SceneSmith/MuJoCo scripted baseline that proves the workcell, physics, scoring,
and execution plumbing. It is not a MolmoAct2 neural-policy rollout.

Run a local LeRobot VLA probe from the generated SceneSmith observation:

```bash
HF_HUB_DISABLE_XET=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
  external/leLab/.venv/bin/python scripts/robot_lab/run_lerobot_policy_probe.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --output-dir outputs/robot_lab/so101_desk_cube_sort \
  --policy-repo lerobot/smolvla_base \
  --device mps \
  --local-files-only \
  --output-json outputs/robot_lab/so101_desk_cube_sort/lerobot/policy_probe_smolvla_mps.json
```

The current verified local VLA path is `lerobot/smolvla_base` on Apple's MPS
backend. The probe loads LeRobot's policy/preprocessor/postprocessor stack,
feeds SceneSmith camera renders plus the SO-101 state/task, and records the
returned six-value action vector. MolmoAct2 is not used in the live loop yet:
its outer LeRobot checkpoint is cached, but the inner
`allenai/MolmoAct2-SO100_101` checkpoint fetch/load was not responsive enough
for the browser action server on this Mac during verification.

Run the Physical Intelligence PI05 LeRobot port on MPS:

```bash
HF_HUB_DISABLE_XET=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
  external/leLab/.venv/bin/python scripts/robot_lab/run_lerobot_policy_probe.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --output-dir outputs/robot_lab/so101_desk_cube_sort \
  --policy-repo lerobot/pi05_base \
  --device mps \
  --local-files-only \
  --num-steps 2 \
  --output-json outputs/robot_lab/so101_desk_cube_sort/lerobot/policy_probe_pi05_mps.json
```

The current PI05 proof loads `lerobot/pi05_base` on MPS from the real
14,467,165,872-byte `model.safetensors` checkpoint, builds the PaliGemma
tokenizer-backed preprocessor stack, loads all checkpoint keys successfully,
and emits a 32-value action. Cold load latency was about 140 seconds; measured
model inference latency after load was about 1.8 seconds. PaliGemma/Gemma
license access must be accepted for the active Hugging Face account before
this path can load the tokenizer.

Replay the PI05 action through the SceneSmith MuJoCo workcell:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/run_sort_policy.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/policy_run_pi05_probe \
  --policy-kind local_lerobot_pi05_policy_backed_controller \
  --policy-probe-json outputs/robot_lab/so101_desk_cube_sort/lerobot/policy_probe_pi05_mps.json
```

The current replay writes `policy_run_pi05_probe/policy_run_summary.json` and
sorts all 4 cubes into matching trays while recording the PI05 neural action
as applied to the robot-control stream.

## PI05 Fine-Tuning Smoke Path

Export a SceneSmith-generated SO-101 desk-sort dataset in LeRobot format:

```bash
HF_HUB_DISABLE_XET=1 \
  external/leLab/.venv/bin/python scripts/robot_lab/export_pi05_finetune_dataset.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --trajectory-json outputs/robot_lab/so101_desk_cube_sort/policy_run_physical_wrist_camera_seed/policy_trajectory.json \
  --output-root outputs/robot_lab/so101_desk_cube_sort/datasets/pi05_smoke_physical_wrist \
  --repo-id gauntlet/scenesmith-so101-pi05-smoke-physical-wrist \
  --episodes 4 \
  --frames-per-waypoint 4 \
  --overwrite \
  --verify
```

The current export writes
`datasets/pi05_smoke_physical_wrist/scenesmith_export_summary.json` and
verifies 4 episodes, 256 frames, three 224x224 image observations, a 32-value
state vector, and a 32-value action vector. The export summary records the
image sources: `render-cam0-side.png`, `render-cam2-wrist.png`, and
`render-cam1-overhead.png`.

Run a one-step PI05 action-expert fine-tune locally on Apple MPS:

```bash
HF_HUB_DISABLE_XET=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
  external/leLab/.venv/bin/python -m lerobot.scripts.lerobot_train \
  --dataset.repo_id=gauntlet/scenesmith-so101-pi05-smoke-physical-wrist \
  --dataset.root=outputs/robot_lab/so101_desk_cube_sort/datasets/pi05_smoke_physical_wrist \
  --dataset.eval_split=0.0 \
  --policy.path=lerobot/pi05_base \
  --policy.device=mps \
  --policy.dtype=float32 \
  --policy.push_to_hub=false \
  --policy.train_expert_only=true \
  --policy.freeze_vision_encoder=true \
  --policy.gradient_checkpointing=true \
  --policy.compile_model=false \
  --steps=1 \
  --batch_size=1 \
  --num_workers=0 \
  --log_freq=1 \
  --save_freq=1 \
  --save_checkpoint=true \
  --env_eval_freq=0 \
  --eval_steps=0 \
  --wandb.enable=false \
  --output_dir=outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_physical_wrist_mps_1step
```

The current physical mounted wrist-camera Mac proof completed the training step
on MPS and wrote this local LeRobot checkpoint:

```text
outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_physical_wrist_mps_1step/checkpoints/000001/pretrained_model
```

Reload the fine-tuned checkpoint through the SceneSmith PI05 runtime bridge:

```bash
HF_HUB_DISABLE_XET=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
  external/leLab/.venv/bin/python scripts/robot_lab/run_lerobot_policy_probe.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --output-dir outputs/robot_lab/so101_desk_cube_sort \
  --policy-repo outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_physical_wrist_mps_1step/checkpoints/000001/pretrained_model \
  --device mps \
  --local-files-only \
  --num-steps 2 \
  --output-json outputs/robot_lab/so101_desk_cube_sort/lerobot/policy_probe_pi05_smoke_physical_wrist_finetuned_mps.json
```

Replay that fine-tuned policy probe through the generated MuJoCo workcell:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/run_sort_policy.py \
  --scene-json outputs/robot_lab/so101_desk_cube_sort/scene.json \
  --xml outputs/robot_lab/so101_desk_cube_sort/mujoco/scene.xml \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/policy_run_pi05_smoke_physical_wrist_finetuned_probe \
  --policy-kind local_lerobot_pi05_smoke_physical_wrist_finetuned_policy_backed_controller \
  --policy-probe-json outputs/robot_lab/so101_desk_cube_sort/lerobot/policy_probe_pi05_smoke_physical_wrist_finetuned_mps.json
```

The current replay writes
`policy_run_pi05_smoke_physical_wrist_finetuned_probe/policy_run_summary.json`
and sorts all 4 cubes while recording the fine-tuned local PI05 checkpoint
action as applied to the robot-control stream. The probe report records the
three input image roles and paths, including `wrist: render-cam2-wrist.png`.

## Visual Action Server

Start the local visual action-server tab:

```bash
./.venv/bin/python scripts/robot_lab/robot_action_server.py \
  --host 127.0.0.1 \
  --port 8822 \
  --output-dir outputs/robot_lab/so101_desk_cube_sort \
  --mujoco-python ./.mujoco_venv/bin/python \
  --lerobot-python external/leLab/.venv/bin/python \
  --policy-repo lerobot/smolvla_base \
  --policy-device mps
```

Open:

```text
http://127.0.0.1:8822/
```

The page loads the SO-101 URDF/STL mesh, shows a plus button, and calls
`POST /api/episodes` when clicked. Each episode first runs a local LeRobot
SmolVLA inference on MPS, records the neural action in
`episodes/<id>/neural_policy_probe.json`, then runs the SceneSmith MuJoCo
task controller and animates the returned trajectory in the browser. This is a
policy-backed controller integration, not evidence that the zero-shot SmolVLA
base checkpoint has learned this generated cube-sorting task end to end.

Verify the visual interaction:

```bash
node scripts/robot_lab/verify_robot_action_server.mjs \
  --url http://127.0.0.1:8822/ \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/action-server-proof-smolvla
```

The verifier now requires a passing browser episode, a passing neural policy
probe, 4/4 sorted cubes, no console errors, and the real SO-101 URDF mesh load.
The current proof selected `lerobot/smolvla_base`, ran on `mps`, sorted 4/4
cubes, and loaded 17 mesh objects with 398,884 triangles.

To run the same visual server with the PI05 Physical Intelligence port:

```bash
HF_HUB_DISABLE_XET=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
  ./.venv/bin/python scripts/robot_lab/robot_action_server.py \
  --host 127.0.0.1 \
  --port 8822 \
  --output-dir outputs/robot_lab/so101_desk_cube_sort \
  --mujoco-python ./.mujoco_venv/bin/python \
  --lerobot-python external/leLab/.venv/bin/python \
  --policy-repo lerobot/pi05_base \
  --policy-device mps
```

```bash
node scripts/robot_lab/verify_robot_action_server.mjs \
  --url http://127.0.0.1:8822/ \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/action-server-proof-pi05 \
  --episode-timeout-ms 360000
```

The current PI05 visual proof selected `lerobot/pi05_base`, ran on `mps`,
sorted 4/4 cubes, loaded 17 SO-101 mesh objects with 398,884 triangles, and
wrote `action-server-proof-pi05/action-server-proof.json` plus
`action-server-proof-pi05/action-server-after-episode.png`.

To run the visual server with the locally fine-tuned PI05 checkpoint:

```bash
HF_HUB_DISABLE_XET=1 PYTORCH_ENABLE_MPS_FALLBACK=1 \
  ./.venv/bin/python scripts/robot_lab/robot_action_server.py \
  --host 127.0.0.1 \
  --port 8822 \
  --output-dir outputs/robot_lab/so101_desk_cube_sort \
  --mujoco-python ./.mujoco_venv/bin/python \
  --lerobot-python external/leLab/.venv/bin/python \
  --policy-repo outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_physical_wrist_mps_1step/checkpoints/000001/pretrained_model \
  --policy-device mps
```

```bash
node scripts/robot_lab/verify_robot_action_server.mjs \
  --url http://127.0.0.1:8822/ \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/action-server-proof-pi05-smoke-physical-wrist-mounted-finetuned \
  --episode-timeout-ms 360000
```

The legacy plus-button visual proof selected and probed the local checkpoint on
`mps`, then used the scripted sorting controller for its 4/4 cube animation. It
is not a neural closed-loop task-success claim. That proof loaded 17 SO-101
mesh objects with 398,884 triangles, verified the visible wrist camera is
attached to the browser `gripper` link, rendered side/wrist/overhead
thumbnails, had no browser console errors, and wrote
`action-server-proof-pi05-smoke-physical-wrist-mounted-finetuned/action-server-proof.json`
plus
`action-server-proof-pi05-smoke-physical-wrist-mounted-finetuned/action-server-after-episode.png`.

The real neural browser path is `randomized` with `PI0.5 live`. Its verifier
confirmed per-step MPS actions reached contact physics without scripted object
motion, then returned the current checkpoint's `neural_policy_stalled` outcome
as an inspectable episode rather than a server exception:

```text
outputs/robot_lab/so101_desk_cube_sort/action-server-neural-proof/action-server-proof.json
outputs/robot_lab/so101_desk_cube_sort/action-server-neural-proof/action-server-after-episode.png
```

To run the randomized intervention browser proof:

```bash
node scripts/robot_lab/verify_robot_action_server.mjs \
  --url http://127.0.0.1:8822/ \
  --mode randomized \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/action-server-proof-randomized-intervention \
  --episode-timeout-ms 360000
```

The current randomized browser proof used seeds `2601` and `2602`, forced a
wrong-tray failure in each deterministic harness episode, recovered with 12
control-step `simulated_leader` frames per episode, sorted 4/4 cubes, kept
`physical_follower_commanded=false`, verified the AprilTag and mounted wrist
camera, and had no browser console errors. The full operator and dataset
contract is in `docs/so101-domain-randomized-interventions.md`.

```text
outputs/robot_lab/so101_desk_cube_sort/action-server-intervention-proof-final/action-server-proof.json
outputs/robot_lab/so101_desk_cube_sort/action-server-intervention-proof-final/action-server-after-episode.png
```

The standalone proof episode and dataset export are:

```text
outputs/robot_lab/so101_desk_cube_sort/intervention_eval_proof/randomized-episode-2401/intervention_episode_summary.json
outputs/robot_lab/so101_desk_cube_sort/datasets/intervention_seed_2401/scenesmith_intervention_export_summary.json
```

## Current Limitations

- The parser is deterministic and task-specific for the desk/tray/cube sorting lane.
- The generated viewer is inspectable and 3D; the robot-operable backend is the MuJoCo XML.
- Real MolmoAct2 execution is still not in the live loop; the practical local
  policy path is the persistent PI05 MPS action service.
- The Studio-brokered physical leader has driven the simulated SO-101 under a
  fresh deadman. A human contact grasp/place correction has not yet been
  performed, so `contact_physics_verified` remains false for that smoke.
- The policy-backed action server runs real LeRobot inference, but task-level
  cube sorting is still completed by a SceneSmith controller in the deterministic
  harness. The separate neural contact-physics mode applies real PI05 actions
  without scripted object motion and currently detects `neural_policy_stalled`,
  as expected from the one-step smoke checkpoint. Robust grasp dynamics still
  require physical-leader correction demonstrations and another fine-tune.
- This bridge deliberately avoids the local Linux/NVIDIA-only SAM3D path on Apple Silicon.
