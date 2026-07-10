# SceneSmith SO-101 Domain-Randomized Interventions

SceneSmith owns the generated workcell, randomized MuJoCo reset, cameras,
physics, scoring, intervention arbitration, and dataset capture. LeRobot owns
the PI0.5 runtime and dataset format. The existing SO-101 Studio service is the
preferred physical-leader broker because it already owns the serial buses.

## Proof States

| Surface | Current proof | Meaning |
|---|---|---|
| AprilTag fiducial | `tag36h11` ID 0, Hamming 0, decision margin 224.79 | Canonical 10x10 marker geometry independently decoded from the MuJoCo overhead render. |
| Randomized scripted harness | 3/3 episodes, 4/4 cubes, 180 synchronized frames | Deterministic pipeline and failure/recovery proof; object motion is scripted and is not a training demonstration. |
| Persistent PI0.5 on MPS | Real SceneSmith observation accepted; first action 1.51 s, queued actions 12 ms and 11 ms | The local checkpoint is loaded once and can drive the control loop. |
| Neural contact-physics episode | PI0.5 actions applied; `neural_policy_stalled` detected | Honest expected failure of the one-step smoke checkpoint; no object teleportation. |
| Neural browser path | `PI0.5 live` selected; MPS policy actions reached MuJoCo; expected task failure returned as an inspectable episode | The UI-to-action-server-to-policy path is real and no longer converts normal task failure into HTTP 500. |
| Studio leader bridge | Five read-only samples plus eight deadman-gated MuJoCo intervention frames | The connected leader controls simulated joints without SceneSmith opening either serial port. |
| Human contact correction | Ready for operator use | A person still needs to move the leader through a real grasp/place correction; no contact success is claimed yet. |

## Recommended Runtime

Keep the persistent PI0.5 service running so the model loads only once:

```bash
external/leLab/.venv/bin/python scripts/robot_lab/local_policy_action_server.py \
  --host 127.0.0.1 \
  --port 8833 \
  --policy-repo outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_physical_wrist_mps_1step/checkpoints/000001/pretrained_model \
  --device mps
```

Run the SceneSmith operator surface:

```bash
./.venv/bin/python scripts/robot_lab/robot_action_server.py \
  --host 127.0.0.1 \
  --port 8822 \
  --output-dir outputs/robot_lab/so101_desk_cube_sort \
  --mujoco-python ./.mujoco_venv/bin/python \
  --lerobot-python external/leLab/.venv/bin/python \
  --policy-repo outputs/robot_lab/so101_desk_cube_sort/train/pi05_smoke_physical_wrist_mps_1step/checkpoints/000001/pretrained_model \
  --policy-device mps
```

Open `http://127.0.0.1:8822/` and choose:

- Policy: `PI0.5 live`
- Correction: `studio leader`
- Enable `arm`
- Set the seed, batch size, and maximum policy steps
- Click `randomized`
- When failure is reported, press and hold `hold to intervene` while moving the physical leader
- Release the button to return control to the policy

The side, wrist, and overhead observations update while the episode runs. The
3D SO-101 joint state and cube states are polled from the same episode progress
record used by the dataset writer.

## Safety Boundary

`studio_leader` calls only `GET http://127.0.0.1:8790/api/parity`. It does not
open a serial device or submit a Studio job. SceneSmith never instantiates a
follower class and never sends a follower action.

`physical_leader` is a fallback for times when the leader serial port is free.
It rejects the known follower port before importing the LeRobot hardware
class. Its direct connection only reads calibrated present positions; it does
not call motor configuration, calibration writes, feedback, or action sends.

The browser deadman must be:

- armed;
- actively held;
- refreshed within 550 ms.

A stale or released deadman returns control to the policy immediately. Joint
targets are clamped to the SO-101 MuJoCo ranges and slew-limited across the
takeover boundary.

## Randomization Contract

Every seed creates a validated reset with:

- collision-aware tray and cube positions;
- cube size and mass variation;
- room, floor, and desk color variation;
- applied MuJoCo friction variation;
- applied key-light intensity variation;
- applied side and overhead camera-position variation;
- deterministic observation brightness and sensor noise;
- fixed robot mount, wrist-camera extrinsics, and AprilTag world anchor.

Invalid placements fail reset sampling instead of entering evaluation.
`domain_randomization_manifest.json` records sampled values and the values
actually patched into `scene.xml`.

## Frame Contract

Each frame represents:

```text
observation(t) -> policy_action(t) + optional human_action(t)
               -> executed_action(t) -> transition.next_state(t+1)
```

It includes side/wrist/overhead image paths, six-joint state, policy proposal,
human proposal, executed target, intervention mask and event, deadman freshness,
failure reason, randomization seed, cube states, and named robot-cube contacts.

## Dataset Export

Real correction fine-tuning should use the default `intervention_only`
selection. This excludes failed policy actions from the imitation target:

```bash
external/leLab/.venv/bin/python scripts/robot_lab/export_intervention_dataset.py \
  --batch-summary <physical-leader-batch>/intervention_batch_summary.json \
  --output-root outputs/robot_lab/so101_desk_cube_sort/datasets/physical-corrections \
  --overwrite \
  --verify
```

The exporter refuses scripted/simulated episodes unless
`--allow-scripted-harness` is explicit. `--frame-selection all` is intended
only for replay, debugging, or pipeline verification.

## Verification

```bash
./.mujoco_venv/bin/python tests/unit/test_robot_lab_intervention.py
./.mujoco_venv/bin/python tests/unit/test_robot_lab_scene_builder.py

./.mujoco_venv/bin/python scripts/robot_lab/verify_intervention_batch.py \
  --batch-summary outputs/robot_lab/so101_desk_cube_sort/intervention-proof/intervention_batch_summary.json \
  --expected-episodes 3 \
  --output-json outputs/robot_lab/so101_desk_cube_sort/intervention-proof/intervention_batch_verification.json

node scripts/robot_lab/verify_robot_action_server.mjs \
  --url http://127.0.0.1:8822/ \
  --mode randomized \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/action-server-intervention-proof-final

node scripts/robot_lab/verify_robot_action_server.mjs \
  --url http://127.0.0.1:8822/ \
  --mode neural \
  --output-dir outputs/robot_lab/so101_desk_cube_sort/action-server-neural-proof

/tmp/scenesmith-apriltag-verify/bin/python \
  scripts/robot_lab/verify_apriltag_fiducial.py \
  --image outputs/robot_lab/so101_desk_cube_sort/completion-audit/apriltag-overhead-640.png \
  --tag-id 0 \
  --output-json outputs/robot_lab/so101_desk_cube_sort/completion-audit/apriltag-detection-proof.json

./.mujoco_venv/bin/python scripts/robot_lab/verify_intervention_system.py
```

Important proof artifacts:

```text
outputs/robot_lab/so101_desk_cube_sort/intervention-proof/intervention_batch_verification.json
outputs/robot_lab/so101_desk_cube_sort/intervention-proof/local-policy-server-probe.json
outputs/robot_lab/so101_desk_cube_sort/intervention-proof/studio-leader-readonly-sample.json
outputs/robot_lab/so101_desk_cube_sort/intervention-proof/neural-policy-contact-smoke/neural_policy_smoke_verification.json
outputs/robot_lab/so101_desk_cube_sort/datasets/intervention-proof/scenesmith_intervention_export_summary.json
outputs/robot_lab/so101_desk_cube_sort/action-server-intervention-proof-final/action-server-proof.json
outputs/robot_lab/so101_desk_cube_sort/action-server-neural-proof/action-server-proof.json
outputs/robot_lab/so101_desk_cube_sort/completion-audit/apriltag-detection-proof.json
outputs/robot_lab/so101_desk_cube_sort/completion-audit/intervention-system-completion.json
```

## Training Direction

Use behavior cloning or DAgger-style supervised fine-tuning first. Collect
operator corrections from the randomized neural contact-physics mode, export
only intervention frames, fine-tune PI0.5, then re-run the same held-out seeds.
Move to HIL-SERL only after the task has a reliable reset, reward/success
detector, and short episode horizon.
