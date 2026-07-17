# Slice Brief 234 - F0c Release-Targeted First Training Task Package

**Date:** 2026-07-17

## Objective

Open F0c as the sole active scientific lane, apply the 06:35 owner addendum's
completion-budget stop rule, and package—without executing—the exact first
training task for the sim2claw fork. The package must attack the verified
learned release deficit, preserve the immutable T20.43c-R2 update-10,000
checkpoint and every prior terminal identity, and give the fork an executable
day-one verification command plus an exact future training command.

This slice is design, deterministic validation, documentation, and signed
packaging only. Training remains locked. It may not deserialize checkpoint
tensors, construct or load a model, create an optimizer, run inference or a
rollout, mutate the R0 dataset/statistics, access hardware/camera/serial, use
network/external compute/Brev, reopen F1/F2/F3, create a retry, inspect
receding-10, or weaken strict-v2.

## Completion-budget decision

Assessment time is `2026-07-17T08:35:52-05:00`; the owner cutoff is
`2026-07-17T10:00:00-05:00`, leaving 5,048 seconds. The retained R2 output
timestamps span `23:22:03` to `01:30:55` (7,732 seconds). Its slowest observed
2,500-update interval is 1,983 seconds, implying 1,586.4 seconds for 2,000
updates before any new implementation, authority, acceptance, rollout,
preservation, review, commit, push, or recovery margin. Allocating only 1,200
seconds to each of the four mandatory reviewed boundaries already requires
6,386.4 seconds total, 1,338.4 seconds beyond the available window.

The full boundary therefore does not fit. No marker, checkpoint read, model,
optimizer, training, or rollout may start. F0c becomes the fork's first
training task exactly as the addendum requires.

## Frozen inputs

- Source branch/origin boundary: `8bb39a1da460a1dd269ce0ec5a5d6b74e5cb746a`.
- R2 update-10,000 checkpoint: tree `c77ee362...`, path
  `outputs/robot_lab/t20_43c_r2_act_replacement_run_001/checkpoints/step_10000`,
  `config.json` SHA-256 `1b2ba898...`, `model.safetensors` SHA-256
  `673c87a5...`; read-only and never overwritten.
- R2 immutable terminal identities: marker `dfe3ff05...`, equivalence
  `fdc06297...`, run `82a06083...`, result `bf2c8b46...`, scorecard
  `6f848570...`, retention `e565e17a...`, final `be11a258...`.
- Exact R0 dataset: root
  `outputs/robot_lab/t20_42_r0_generation_run_001/lerobot_dataset`, repo id
  `scenesmith/t20-42-r0-anchor-grasp-train`, result `d238379b...`, mixture
  `37b30d34...`, statistics `02ba0e70...`, 129 episodes / 31,366 frames /
  59,904 windows, with held-out rows excluded.
- Diagnosis: F0 `807d3da7...` (normalization and tail starvation false,
  physical-L1 gripper coefficient 2.696308, release pattern 20 frames late),
  F0a `278e8bc7...` (20/24 source aliases and 17-frame lag), F0b trace/result
  `af62a3b5...`/`8fb34ff4...` (cadence-only negative at frame 219).

## Frozen correction contract

The evidence selects a release-phase-oversampled continuation, not new
post-release data generation: F0 disproved missing tail exposure and proved the
open command lies inside the R0 MEAN_STD envelope. The existing dataset and
statistics remain byte-identical.

1. Load the retained R2 weights exactly once into the unchanged ACT
   architecture; create a fresh AdamW state. Do not modify the source
   checkpoint.
2. Keep batch 8, seed `20260801`, MPS/fp32, learning rates `1e-5` for policy
   and backbone, weight decay `1e-4`, gradient clip `10.0`, no scheduler, and
   a hard ceiling of 2,000 optimizer updates.
3. Give starts whose source phase is `release` or `release_settle` importance
   weight `4.0`; every other eligible R0 start has weight `1.0`. Preserve
   episode boundaries, tail padding, held-out exclusion, and a deterministic
   sampler stream. This raises targeted start mass without claiming the base
   mixture was defective.
4. Replace uniform joint reduction only with F0's frozen active-mean-one
   physical-L1 coefficients `[0.013616426547530116, 1.153008898269766,
   0.4279690527814028, 0.7369730539120705, 0.9721244211024305,
   2.6963081473868007]`; apply the action-valid mask before time/joint means.
   KL and every non-action ACT term remain unchanged.
5. Evaluate only chunk-50 at continuation updates `[0, 500, 1000, 2000]` on
   seed-0 episode 0, 244 frames, one queue reset, starts
   `[0,50,100,150,200]`, executed lengths `[50,50,50,50,44]`, and six masked
   terminal actions. Update 0 must reproduce the retained comparator before
   update 1. Receding-10 is out of scope.
6. Strict-v2 is the sole rollout verdict. Stop and preserve immediately on the
   first Gate C pass; otherwise preserve the update-2,000 terminal negative.
   No retry, sweep, threshold amendment, extra seed, or extra checkpoint.

## Authority and proof boundary

Before execution, a fresh implementation commit must be reviewed and exact on
origin. Then materialize a fresh owner-grant attribution, central authority
request/decision, runtime preflight, one-use permit, and separate pre-run
acceptance. `training_lock` may open only when all identities, the immutable
checkpoint tree, exact R0 inputs, stable Python 3.12/LeRobot runtime, renderer,
budget, and remote commit agree. The marker must be written before checkpoint
deserialization and must fail closed if any prior or future F0c artifact exists.

Required terminal evidence includes all finite losses/gradients, sampler and
phase-weight audits, update/checkpoint identities, full decoded chunk tensors,
244 executed actions and observations, strict-v2 per-frame margins, comparator
hashes, signed MP4/manifest, result, scorecard, retention receipt, final receipt,
and independent reconstruction. Outputs remain ignored; compact signed evidence
is tracked. Existing R2/F0/F0a/F0b files are immutable inputs, never rewritten.

## Day-one commands

Validate the frozen package first:

```bash
external/lerobot/.venv/bin/python \
  scripts/robot_lab/write_f0c_release_targeted_package.py --check
external/lerobot/.venv/bin/python -m unittest \
  tests/unit/test_f0c_release_targeted_package.py
```

After the fork implements the reviewed runner and all fresh authority artifacts
are accepted on origin, the sole execution command is frozen as:

```bash
external/lerobot/.venv/bin/python \
  scripts/robot_lab/run_f0c_release_targeted_continuation.py \
  --spec configurations/robot_lab/f0c_release_targeted_continuation_spec.json \
  --started-at "$(date -Iseconds)"
```

The execution entrypoint is a required next-slice deliverable, not present-run
authority. Invoking a similarly named ad-hoc command is prohibited.

## Acceptance

F0c packaging passes when the signed spec reconstructs from immutable inputs;
tests reject checkpoint, dataset, coefficient, phase-weight, evaluation,
budget, authority, and false-success drift; the living state points only to
F0c; and the package plus exact commands are preserved on origin. The reviewer
must close this source-repo slice as `packaged_for_fork_day_one`, not as a
training result or Gate C attempt.
