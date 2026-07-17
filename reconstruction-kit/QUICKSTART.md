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
recorded in `docs/reconstruction/SOURCE_MANIFEST.json`, but no external
checkouts, model weights, or authority. The signed asset pack does include the
exact 10-episode base dataset and three simulation-only trace fixtures.

## Stage 1 — Run the one-command bootstrap

For an offline rehearsal beside the source checkout, run this before adding any
new unreceipted file to the export:

```bash
python3 tools/bootstrap.py \
  --local-source-root /absolute/path/to/sim-link \
  --offline
```

On a new machine with network access, omit both flags. Add
`--include-optional-lelab` only if the UI/URDF reference is needed.

The command fails closed unless it can:

1. verify the pristine export receipt and asset identity;
2. clone the exact LeRobot and SO-ARM100 revisions and verify the tracked patch;
3. build the pinned Python 3.12 runtime and exact critical package versions;
4. verify the executable LeRobot stack and focused model-free tests;
5. generate one unassisted strict-v2 seed-0 expert episode; and
6. render a one-frame MP4/manifest from each retained T20.43, T20.43b, and
   T20.44 trace schema.

It writes a signed receipt under
`outputs/reconstruction/bootstrap_run_001/`. It creates no optimizer, accesses
no hardware, and grants no authority.

The verified package target is:

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

W1 intentionally proves the exported source stack's existing dual-runtime
composition. After the fork is born, collapse to this pinned LeRobot venv as
the sole interpreter and render in-process; delete the subprocess dispatch
layer instead of carrying it forward.

## Stage 2 — Reach data parity

The asset pack carries the exact 10-episode/2,330-frame base in 63 MB of
content-addressed chunks, not the 2.7 GB full R0 output tree. Verify or
materialize it with:

```bash
external/lerobot/.venv/bin/python tools/portable_assets.py verify
external/lerobot/.venv/bin/python tools/portable_assets.py materialize-base
```

The turnkey full-R0 regeneration command is integrated only after its isolated
W2 candidate and rehearsal receipt pass review. Until then, do not improvise by
executing copied historical T20.42 grants or permits.

The expected R0 boundary is 119 new training strict successes, 9 fresh held-out
strict successes, 129 total training episodes, 31,366 frames, and 59,904
windows. Any mismatch is a new dataset, not a recreation.

Portable parity requires exact candidate order, episode content, native dataset
manifest, compiler/window content, held-out exclusion, and statistics semantics.
Fresh execution IDs, paths, timestamps, and permit-bound wrapper identities are
expected to differ. Reusing old authority just to force their hashes to match is
forbidden.

## Stage 3 — Reach policy-result parity

After runtime and R0 parity, freeze the evaluation seeds before training. The
fork opens only two primary tracks:

- ACT as the imitation baseline; and
- state-based RL on joint state plus simulator object pose, light parquet, and
  60-frame success-terminated reach/push tasks.

Training may be accelerator-nondeterministic. Every candidate is judged by the
separately owned CPU/fp32 evaluator, whose verdict must be bit-identical across
Macs and Linux. Every run emits `RUN_RECEIPT.json` with commit, config hash,
dataset identity, seed, wall clock, and metrics, plus replayable artifacts.

SmolVLA and PI0.5 are day-three stretch tracks only. Historical T20.43b,
original T20.43c, and T20.43c-R2 permits are consumed/inert. The original
update-728 interruption remains inconclusive; R2 is the later full ACT terminal
negative. Neither licenses a continuation or third ACT attempt in the fork.

Model weights and checkpoints are not in this kit. Obtain them through their
own licensed, checksum-bound process, and keep raw-byte identities in the new
repo’s runtime preflight rather than in prose.

## Stage 4 — Physical work, later

Physical work remains closed until metric calibration and a real Robo Scan
handoff are validated. In the fork, teleop, tests, and the demo all use the one
reviewed robot gateway; no direct second hardware path is allowed. Never infer
motion authority from a run receipt, a no-prompt shell setting, copied source-
repo authority, or successful simulation.

Read [RGB camera hardware readiness](./HARDWARE_READINESS_RGB_CAMERAS.md)
before planning camera work. The retained census is a terminal failure, not a
current D405 or C922 mode/latency qualification.
