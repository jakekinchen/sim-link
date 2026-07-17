# F1 pi05 R0 full fine-tune closeout

## Verdict

The sole authorized 5,000-step `pi05_base` full fine-tune completed. All five fixed checkpoints were evaluated under chunk-50 and receding-10 semantics in CPU MuJoCo. No rollout passed the strict simulation grasp cycle, so this lane produced policy-training evidence and a selected partial-lift checkpoint, not a promoted policy or physical proof.

The frozen selection rule chose checkpoint 1,000 under chunk-50: 37.519 mm maximum lift, `lifted_without_strict_cycle`, failing only `grasp_hold_strict_v2`.

## Frozen identities

- Source commit: `471b7582a756e618aebd37845adcaccde880741d`
- R0 manifest: `bd36b7c491ba3c3e08ae3efd87febdbbb1f52f917cb258399484ba4f5311a184`
- R0 mixture: `37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df`
- R0 statistics: `02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae`
- Frozen W2 dataset tree: `3ea03babc3c2ad7585b829dd858b15f09045edd106d0beba8d75540c403eebb8`
- Base model revision: `7de663972b7817d2c4cf2d84c821153dfea772e9`
- Base model raw weights: `0eb11ca9587678c1d2ef8cf32807c29f8ce53a2bfdfc1aa4a4c96f16fca59b0f`
- Pinned stack identity: `c8e903e7f1b75215864719398c902d864d8cbd7f43e01f03ffb22c8de240a7a4`

The completed W2 scratch dataset was used under its reviewed receipt route. It matched the required semantic identities but was not claimed byte-identical to the older retention tree.

## Launch

```sh
env F1_ROOT=/home/shadeform/sim-link-f1 bash /home/shadeform/sim-link-f1/scripts/run_train.sh
```

Materialized config: `scripts/run_train.sh` and `config/F1_PREFLIGHT.json`. The run used full fine-tuning, batch 8, bfloat16, gradient checkpointing, model compilation, seed 20260717, and checkpoints every 1,000 steps. Run count was one with no training retry.

## Fixed-checkpoint evaluation

| Step | Semantics | Lift (mm) | Terminal outcome | Strict |
|---:|---|---:|---|---|
| 1,000 | chunk-50 | 37.519 | lifted without strict cycle | no |
| 1,000 | receding-10 | 1.580 | contact without strict lift | no |
| 2,000 | chunk-50 | 34.458 | lifted without strict cycle | no |
| 2,000 | receding-10 | 19.316 | contact without strict lift | no |
| 3,000 | chunk-50 | 33.656 | lifted without strict cycle | no |
| 3,000 | receding-10 | 34.609 | lifted without strict cycle | no |
| 4,000 | chunk-50 | 29.106 | lifted without strict cycle | no |
| 4,000 | receding-10 | 11.058 | contact without strict lift | no |
| 5,000 | chunk-50 | 2.026 | contact without strict lift | no |
| 5,000 | receding-10 | 35.575 | lifted without strict cycle | no |

The first evaluator startup failed before any rollout because headless GLFW had no `DISPLAY`. Its log was preserved. A bounded EGL renderer preflight passed, then the required evaluator completed once with `MUJOCO_GL=egl PYOPENGL_PLATFORM=egl`. This was not a training retry.

## Selected artifact

- Location: `/Volumes/cerebro/CodexOffload/f1-pi05-r0-20260717/checkpoint-001000/pretrained_model`
- Model SHA-256: `755544956570297f09f72c48874f5dc9643e02f14a0c934109b81a9e66aec7fb`
- Config SHA-256: `1f17178a8bf1a7d62f9ef89673b79eb4ef839158485e5c09dda2ad9c4eb125d9`
- Files: 7; copied model and sidecars only, excluding optimizer state and other checkpoints

No reusable F2 endpoint was created or left live because no strict simulation grasp succeeded.

## Cost and teardown

- Brev type: `massedcompute_A100_sxm4_80G_DGX`, one A100-80GB, displayed `$1.656/hour`
- Created: 2026-07-17 02:50:44 CDT
- Delete requested: 2026-07-17 06:10:23 CDT
- Deletion confirmed: 2026-07-17 06:10:58 CDT
- Duration: 3.337222 hours
- Displayed-rate spend calculation: `$5.526` (not a provider invoice)
- Final inventory: `workspaces: null`; zero remaining resources

The canonical checkout was read-only throughout F1. It was sourced at commit `471b758`; its live HEAD later advanced independently in another lane.

## Evidence index

- `receipts/RUN_RECEIPT.json` — identity `ca9a23b183c9854266d3960b66bc60f0d7cf4aea8d0dc40ad96293e9201d8716`
- `receipts/REMOTE_PREFLIGHT.json` — identity `edcd861f70613517bf3aabc50f49f385b356c52238a5a3601114006947b1c962`
- `receipts/LAUNCH_RECEIPT.json` — identity `7e1698fcf8b22bffbc47bf0c5bf01e9bbd3c86e4e48d4cd5c73799dfe63ffc99`
- `outputs/evaluations/EVALUATION_SUMMARY.json` — identity `992cf3fdd3f12c8543b643000691504003a080ff063fbedf98992425ab7a0b50`
- `receipts/SPEND_LEDGER.json` — identity `c949abbf50fea57513bd6a67899f6544cb5d9a99b05cd9bc63354fec6a3cecd9`
- `receipts/TEARDOWN_INVENTORY_RECEIPT.json` — identity `7343ad9fc1bc1802ec00bd13eab65807ca2d41818c8d59210957b980b2b66064`

All listed signed JSON identities and the ten individual rollout identities were recomputed successfully after copy.
