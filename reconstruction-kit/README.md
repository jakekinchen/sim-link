# SO-101 Simulation Learning Reconstruction Kit

This directory is the compressed, portable handoff for the SO-101/MuJoCo/
LeRobot program developed inside SceneSmith. It is designed to be copied into a
new repository without copying the full numbered experiment history, private
observations, datasets, checkpoints, ignored outputs, or expired authority.

## Honest status in one paragraph

The simulation/data/evidence substrate works: deterministic constructive
grasps pass strict-v2, R0 contains 129 training episodes and 31,366 frames, and
the processor, coordinate, authority, renderer, trace, and receipt boundaries
are verified. Learned-policy task success is not solved. SmolVLA completed one
5,000-update campaign and failed Gate C, though its strongest partial reached
18.061 mm lift. The corrected 10,000-update ACT replacement is implemented and
pre-run accepted, but its one-use marker was never created; it needs a fresh
owner window and administrative authority epoch. No physical-transfer or
promotion claim exists.

## Reading order

1. [Current state](./CURRENT_STATE.md) — what is actually proven now.
2. [Architecture](./ARCHITECTURE.md) — the minimal system, data, and authority
   spine.
3. [Quick start](./QUICKSTART.md) — export a seed repository and reach evidence,
   runtime, data, and policy parity in safe stages.
4. [Results and lessons](./RESULTS_AND_LESSONS.md) — what worked, what failed,
   and which tempting directions should stay closed.
5. [Forward plan](./FORWARD_PLAN.md) — the dependency-ordered route from the
   unconsumed ACT rung to learned Gate C and eventual physical work.
6. [Third-party boundary](./THIRD_PARTY.md) — exact external pins, licenses, and
   what is deliberately not copied.

`CURRENT_STATE.json` is the compact machine-readable snapshot.
`SOURCE_MANIFEST.json` is generated from `source-selection.json` and binds every
curated source byte to closeout commit `6c53d93...`.

## Verify and export

From the `sim-link` repository root:

```bash
python3 reconstruction-kit/scripts/kit.py build-manifest --check
python3 reconstruction-kit/scripts/kit.py verify
python3 -m unittest reconstruction-kit/tests/test_kit.py
python3 reconstruction-kit/scripts/kit.py export ../so101-reconstruction
python3 ../so101-reconstruction/tools/reconstruction_kit.py \
  verify-export ../so101-reconstruction
```

The exporter requires a new destination outside this repository. It copies the
curated Git objects plus the kit, emits `RECONSTRUCTION_RECEIPT.json`, and fails
closed on hash drift, symlinks, traversal, collisions, extra files, or authority
escalation.

## What this kit is not

- It is not a trained-policy release.
- It does not include external repositories, model weights, checkpoints,
  optimizer state, datasets, camera frames, hardware receipts, or rendered
  campaign media.
- It does not transfer training, hardware, physical-motion, external-compute,
  or promotion authority.
- It does not make old owner grants or one-use permits valid in the new repo.
- It is not a reason to replay the T20.35 optimizer alphabet. The useful
  mechanisms and negative findings are already distilled here.
