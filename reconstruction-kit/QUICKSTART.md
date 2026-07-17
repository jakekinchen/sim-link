# Quick Start to the Same Proof Boundary

The fastest honest route has four stages. Stop at the stage you actually need.
Evidence parity is cheap; policy parity is not.

## Stage 0 — Export the seed repository

From this `sim-link` checkout:

```bash
python3 reconstruction-kit/scripts/kit.py build-manifest --check
python3 reconstruction-kit/scripts/kit.py verify
python3 reconstruction-kit/scripts/kit.py export ../so101-reconstruction
python3 ../so101-reconstruction/tools/reconstruction_kit.py \
  verify-export ../so101-reconstruction
```

The destination must not exist and must be outside the source repo. Inspect
`RECONSTRUCTION_RECEIPT.json` before initializing a new Git history.

```bash
cd ../so101-reconstruction
git init
git add -- .
git commit -m "Seed SO-101 reconstruction from verified SceneSmith capsule"
```

At this point you have exact compact source parity with portable boundary
`605e4d3...` and an evidence-state snapshot from `6c53d93...`, but no external
packages, datasets, weights, or authority.

## Stage 1 — Recreate the pinned local runtime

Acquire external repositories separately at the exact pins in
`docs/reconstruction/THIRD_PARTY.md`:

```bash
mkdir -p external
git clone https://github.com/huggingface/lerobot.git external/lerobot
git -C external/lerobot checkout e40b58a8dfa9e7b86918c374791599d070518d11
git -C external/lerobot apply ../../scripts/robot_lab/patches/pi05_gripper_loss_weight.patch

git clone https://github.com/TheRobotStudio/SO-ARM100.git external/SO-ARM100
git -C external/SO-ARM100 checkout fda892cba81032c46c40976a48c9ceadbf40a9ca

# Optional UI/URDF reference only
git clone https://github.com/huggingface/leLab.git external/leLab
git -C external/leLab checkout def3e9e51e99c03e01b214dc8a0d9b7c2dd5f0da
```

These are network and install instructions, not actions performed by the kit.
Verify the patch and source hashes before installing anything:

```bash
python3 scripts/robot_lab/verify_lerobot_stack.py
```

The last verified runtime target was:

| Package | Version |
| --- | --- |
| Python | 3.12.12 |
| LeRobot | 0.6.1 at the pinned commit plus one tracked patch |
| PyTorch / torchvision | 2.11.0 / 0.26.0 |
| MuJoCo | 3.3.5 |
| datasets | 4.8.5 |
| NumPy | 2.2.6 |
| Pillow | 12.3.0 |
| PyArrow | 25.0.0 |

Use the pinned LeRobot checkout as the runtime environment; do not install the
full original SceneSmith paper stack just to run the robotics capsule. After
creating the environment, run the focused model-free suite first:

```bash
python -m unittest \
  tests.unit.test_artifact_contract \
  tests.unit.test_authority_composer \
  tests.unit.test_so101_coordinates \
  tests.unit.test_so101_processor \
  tests.unit.test_strict_grasp_v2 \
  tests.unit.test_lerobot_stack
```

## Stage 2 — Reach data parity

The export includes compact manifests, statistics, construction code, and
receipts—not the 31,366-frame dataset or ignored output tree. Choose one route:

1. Regenerate R0 from the exact construction spec and seeds using a new local
   authority epoch, or
2. Move a separately packaged dataset bundle only after its tree identity,
   mixture, statistics, held-out exclusion, and receipt independently match.

The expected R0 boundary is 119 new training strict successes, 9 fresh held-out
strict successes, 129 total training episodes, 31,366 frames, and 59,904
windows. Any mismatch is a new dataset, not a recreation.

Do not execute the copied T20.42/T20.43b/T20.44 owner grants or permits. They are
historical, repository-bound, and expired. Create new authority artifacts with
new paths/identities after reviewing the new repo’s source commit and output
absence.

## Stage 3 — Reach policy-result parity

Only after runtime and R0 parity:

- Reproducing the SmolVLA baseline means exactly one 5,000-update run with its
  frozen scheduler/checkpoints and ten dual-semantics rollouts. The expected
  historical result is terminal negative, not success.
- The current forward task is the unchanged ACT 10,000-update recipe with seven
  checkpoints and fourteen rollouts. It requires a full uninterrupted local
  window, a fresh one-use marker, and no retry.
- PI0.5 remains conditional. Do not reopen the historical optimizer alphabet;
  use it only as a compatibility/stress track after ACT evidence exists.

Model weights and checkpoints are not in this kit. Obtain them through their
own licensed, checksum-bound process, and keep raw-byte identities in the new
repo’s runtime preflight rather than in prose.

## Stage 4 — Physical work, later

Physical work remains closed until metric calibration and a real Robo Scan
handoff are validated, the central composer grants the required state, the
owner is present, and a finite hardware permit exists. Never infer motion
authority from a no-prompt shell setting or from successful simulation.
