# SO-101 Simulation Learning Reconstruction Kit

This directory is the compressed, portable handoff for the SO-101/MuJoCo/
LeRobot program developed inside SceneSmith. It is designed to be copied into a
new repository without copying the full numbered experiment history, private
observations, the full R0 dataset, checkpoints, ignored outputs, or expired
authority. It carries only the verified ten-episode base fixture needed to
recreate R0 locally.

## Honest status in one paragraph

The simulation/data/evidence substrate works: deterministic constructive
grasps pass strict-v2, R0 contains 129 training episodes and 31,366 frames, and
the processor, coordinate, authority, renderer, trace, and receipt boundaries
are verified. Learned-policy task success is not solved. SmolVLA completed one
5,000-update campaign and failed Gate C, though its strongest partial reached
18.061 mm lift. Original T20.43c remains an immutable inconclusive ACT
interruption at update 728. T20.43c-R2 then completed the unchanged recipe
through 10,000 updates, seven checkpoints, and fourteen rollouts with no
infrastructure failure and no Gate C pass. Its best chunk-50 lift was 45.674304
mm; the final 37.655304 mm rollout missed only release, while final receding-10
lost the grasp. ACT-on-R0 is therefore a verified terminal negative, not an
unresolved capability, and no retry, physical-transfer, or promotion claim
exists.

## Reading order

1. [Current state](./CURRENT_STATE.md) — what is actually proven now.
2. [Architecture](./ARCHITECTURE.md) — the minimal system, data, and authority
   spine.
3. [Quick start](./QUICKSTART.md) — export a seed repository and reach evidence,
   runtime, data, and policy parity in safe stages.
4. [Results and lessons](./RESULTS_AND_LESSONS.md) — what worked, what failed,
   and which tempting directions should stay closed.
5. [Forward plan](./FORWARD_PLAN.md) — the dependency-ordered fork route through
   bootstrap, ACT/state-RL baselines, learned evaluation, and eventual hardware.
6. [Third-party boundary](./THIRD_PARTY.md) — exact external pins, licenses, and
   what is deliberately not copied.
7. [RGB camera readiness](./HARDWARE_READINESS_RGB_CAMERAS.md) — the reviewed
   D405 terminal failure and exact replacement requirement; no readiness pass.
8. [Hackathon fork annex](../docs/autonomous-workflow/hackathon-fork-annex-2026-07-16.md)
   — optional three-day team plan; direction only, never authority.

`CURRENT_STATE.json` is the compact machine-readable result snapshot at the
final portable source boundary. `SOURCE_MANIFEST.json` is generated from
`source-selection.json` and binds every curated implementation/evidence byte,
including the immutable T20.41 route snapshot and both T20.43c terminal
boundaries, to one portable source commit. Compact R2 result evidence travels;
its expired authority/preflight/permit files and manual runner do not. The
export receipt separately binds the compressed reconciled documentation in
this directory.

## What travels

The kit now includes a signed 66 MB reconstruction asset pack rather than the
2.7 GB R0 output tree: the exact 10-episode/2,330-frame T20.23 base dataset,
chunked below the repository file ceiling, plus one real signed trace from each
T20.43, T20.43b, and T20.44 schema. It carries no model checkpoint, optimizer
state, private observation, full R0 dataset, or authority.

The reviewed K3 RGB-only census note also travels. It records a safe terminal
failure: D405 returned a decoded frame whose dimensions did not match the
signed selected input mode, C922 was not opened, and no frame, mode census,
latency result, or hardware-readiness label was accepted. The private frame and
failure payload do not travel.

`tools/bootstrap.py` is the day-one entrypoint in an exported repo. It verifies
the pristine receipt and asset pack before writing, clones exact dependency
pins from a local source or their upstream URLs, creates the pinned runtime,
verifies the stack, runs focused non-authorizing tests, generates one strict-v2
expert episode, and renders a one-frame smoke from every retained schema. The
source-repository authority composer is retained as inert history but is not
rebuilt in the export because its lock deliberately binds an untracked local
leLab `uv.lock`; manufacturing that dirty checkout would misstate portability
and authority. The source-repo W1 rehearsal must prove the existing
dual-runtime path. At fork birth, the target architecture deliberately
collapses to one LeRobot venv and in-process render.

`tools/regenerate_r0.py` is the reviewed W2 compatibility command. After the
bootstrap passes, it creates a fresh non-live local epoch, materializes the
portable base, runs the unchanged 119+9 constructive generation, rebuilds the
legacy full `LeRobotDataset`, and emits root `RUN_RECEIPT.json`. It passes only
when all 129 episodes, 31,366 frames, 59,904 windows, mixture
`37b30d34...`, statistics `02ba0e70...`, and the lower-level store/compiler/
dataset identities match exactly. Any drift is classified `new dataset, not a
recreation`. The receipt is compatibility evidence, never current authority.
The future light state-only parquet/60-frame RL tier remains a separate
fork-birth follow-on; full audiovisual data remains VLA/demo-only.

The combined clean-export rehearsal now verifies this path end to end. W1
receipt `392fcc8b...` proves the pinned dual-runtime source stack, one
244-frame strict-v2 expert episode, and all three retained render schemas.
W2 receipt `86739578...` then recreates the exact legacy R0 boundary in
4,110.434219 seconds with no mismatches; an independent `verify` exits 0. Both
receipts explicitly keep authority, model construction, optimizer work,
hardware, network, external compute, and Brev false.

After the combined receipt was preserved, the source capsule was re-pinned at
`992ed2f...`. Final manifest `d5396251...`, source-pin validation export
`ae7cfd7c...`, and W1 recheck `7d9fa11a...` all verify. The W2 run is not
repeated merely to make fresh timestamps or wrapper hashes agree; its exact
content gate and receipt remain the decisive data-parity proof.

## Verify and export

From the `sim-link` repository root:

```bash
python3 reconstruction-kit/scripts/kit.py build-manifest --check
python3 reconstruction-kit/scripts/kit.py verify
python3 reconstruction-kit/scripts/portable_assets.py verify
python3 -m unittest reconstruction-kit/tests/test_kit.py
python3 reconstruction-kit/tests/test_regenerate_r0.py
python3 reconstruction-kit/scripts/kit.py export ../so101-reconstruction
python3 ../so101-reconstruction/tools/reconstruction_kit.py \
  verify-export ../so101-reconstruction

# In the pristine export, clone dependency pins locally and rehearse offline.
python3 ../so101-reconstruction/tools/bootstrap.py \
  --local-source-root "$(pwd)" --offline
```

The exporter requires a new destination outside this repository. It copies the
curated Git objects plus the kit, emits `RECONSTRUCTION_RECEIPT.json`, and fails
closed on hash drift, symlinks, traversal, collisions, extra files, or authority
escalation.

The generated manifest records exact file and byte counts at the final source
pin. It explicitly hashes each deliberate bulky historical omission and keeps
the repository-bound live project state out of the export. Omission reasons
remain auditable without transplanting stale authority.

## What this kit is not

- It is not a trained-policy release.
- It does not include external repositories, model weights, checkpoints,
  optimizer state, the full generated R0 dataset, camera frames, hardware
  private receipts, or rendered campaign media. One redacted RGB-census
  failure manifest is included as inert diagnostic history.
- It does not transfer training, hardware, physical-motion, external-compute,
  or promotion authority.
- It does not make old owner grants or one-use permits valid in the new repo.
- It is not a reason to replay the T20.35 optimizer alphabet. The useful
  mechanisms and negative findings are already distilled here.
