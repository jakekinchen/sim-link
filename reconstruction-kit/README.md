# sim2claw Reconstruction Kit

**Simulation to Closed-Loop Autonomous Workcell**

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
exists. The subsequent F0/F0a/F0b chain narrowed that failure without changing
the verdict: tail coverage, open-gripper normalization, and aggregate
late-phase loss mass are not the defect; the policy's release pattern is about
20 frames late amid lift/lower observation aliasing; and one same-checkpoint
hybrid-cadence rollout still had both fingertip pads in contact at release-final
frame 219. Cadence alone is insufficient. No corrective ACT rung or Brev run
was consumed at the F0b/F3 freeze boundary. A later, separately authorized
off-ledger F1 Brev run completed one 5,000-step PI0.5 full fine-tune and ten
rollouts, but its selected 37.519304 mm chunk-50 partial failed strict grasp
hold and zero rollouts passed Gate C. The later owner addendum selected F0c
as the fork's first, one-attempt training task: a release-phase-oversampled,
physical-L1-weighted continuation capped at 2,000 updates. It is packaged but
unexecuted by Reviewer 327; the execution runner and fresh fork authority are
still required.

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
9. [F0c first training task](./F0C_FIRST_TRAINING_TASK.md) — the signed
   post-freeze experiment contract, exact inputs, stop rules, and day-one
   commands; no model result or transferred authority.

The compact canonical F1 pointer remains in the source repository at
`configurations/robot_lab/f1_brev_evidence_fold.json`. The 9.35 GB retained
checkpoint and the off-ledger receipt workspace are deliberately not copied
into this kit.

`CURRENT_STATE.json` is the compact machine-readable result snapshot at the
current portable source boundary. `SOURCE_MANIFEST.json` is generated from
`source-selection.json` and binds every curated implementation/evidence byte,
including both T20.43c terminal boundaries and the later F0/F0a/F0b
localization chain, to one portable source commit. Compact R2 result evidence
and the full replayable F0b trace travel; expired authority/preflight/permit
files and the manual R2 runner do not. The export receipt separately binds the
compressed reconciled documentation in this directory.

## What travels

The kit includes a signed 66 MB reconstruction asset pack rather than the
2.7 GB R0 output tree: the exact 10-episode/2,330-frame T20.23 base dataset,
chunked below the repository file ceiling, plus one real signed trace fixture
from each T20.43, T20.43b, and T20.44 schema. The source capsule additionally
carries F0/F0a diagnostics and the 3.3 MB replayable F0b trace/result bundle.
It carries no model checkpoint, optimizer state, private observation, full R0
dataset, or live authority.

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

The K2 combined clean-export rehearsal verifies this path end to end. W1
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
content gate and receipt remain the decisive data-parity proof. F3 re-verifies
the final capsule/export/bootstrap boundary after folding the release findings,
without pretending documentation changes require another hour-long generation.

F3 source implementation `48970159...` is pinned by commit `8066e59b...` and
manifest `ec9084dc...` (444 selected files, 81,458,869 bytes). Pristine export
`57b4623b...` independently verifies 465 files, and offline W1 bootstrap
`bd2c9575...` passes 29 focused tests, one 244-frame strict-v2 expert episode,
and all three retained renderer schemas. F3 receipt `bf488607...` binds those
facts and the unchanged W2 exact-content receipt without granting authority.
Remote tag `freeze-2026-07-17-hackathon-fork` targets F3 closeout
`04a52929...`; it is a marker, not authority.
F0c is intentionally not smuggled into that frozen manifest. Its exact signed
spec `6a178138...` and explanatory document travel as receipt-bound post-freeze
export-wrapper addenda; the checkpoint remains separately acquired and
checksum-bound.

## Verify and export

From the `sim-link` repository root:

```bash
python3 reconstruction-kit/scripts/kit.py build-manifest --check
python3 reconstruction-kit/scripts/kit.py verify
python3 reconstruction-kit/scripts/portable_assets.py verify
python3 -m unittest reconstruction-kit/tests/test_kit.py
python3 reconstruction-kit/tests/test_regenerate_r0.py
python3 reconstruction-kit/scripts/kit.py export ../sim2claw
python3 ../sim2claw/tools/reconstruction_kit.py verify-export ../sim2claw

# In the pristine export, clone dependency pins locally and rehearse offline.
python3 ../sim2claw/tools/bootstrap.py \
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
- It is not authority to execute F0c. The post-freeze package selects one exact
  fork experiment, but the fork must implement/review the runner, bind the
  immutable checkpoint, and issue fresh native authority before optimizer use.
