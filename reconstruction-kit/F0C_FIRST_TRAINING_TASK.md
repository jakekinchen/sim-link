# F0c — First Fork Training Task

F0c is the first training task selected for the sim2claw fork after the frozen
F3 reconstruction boundary. It is a signed, unexecuted experiment contract—not
a model result, transferred permit, or claim that learned strict-v2 success is
solved.

The canonical machine-readable contract travels at
`configurations/robot_lab/f0c_release_targeted_continuation_spec.json`. Its
signed payload identity is
`6a178138f79236f27adc04b337e0142a5dfa851f1f67d32d55dcc8b41e4da5dd`
and its tracked-file SHA-256 at packaging is
`9ff872537c10e529cbb8618090c887a3cd1e081e1d67910a91a199c99aae9297`.
The F3 source manifest remains frozen; the exact JSON and this document are
receipt-bound export-wrapper addenda and do not silently repin or reopen that
verified capsule.

## Why this is next

R2 completed 10,000 ACT updates and failed only release in its strongest final
chunk-50 rollout. F0 rejected tail starvation, open-gripper normalization, and
aggregate release-mixture underweighting. F0a found lift/lower observation
aliasing and a 17-frame lag. F0b showed that cadence-only re-observation still
left both fingertip pads in contact at the release-final frame. The remaining
bounded discriminator is therefore a release-targeted correction:

- deterministically oversample R0 starts whose source phase is `release` or
  `release_settle` by `4.0`; other eligible starts remain `1.0`;
- apply F0's frozen active-mean-one physical-L1 joint coefficients
  `[0.013616426547530116, 1.153008898269766, 0.4279690527814028,
  0.7369730539120705, 0.9721244211024305, 2.6963081473868007]` after the
  action-valid mask; and
- leave the dataset, statistics, architecture, KL/non-action terms, and
  strict-v2 verdict unchanged.

This is a preregistered one-attempt experiment. It is not permission for an
optimizer alphabet or another receding-10 investigation.

## Exact inputs

- Immutable R2 update-10,000 checkpoint tree:
  `c77ee36250f921dbdfc7b19802ab8705c9795b298fa14d4a2b1825acf68451ab`.
  `config.json` is `1b2ba898...`; `model.safetensors` is `673c87a5...` and
  206,494,928 bytes. The checkpoint is deliberately not copied by this kit;
  acquire it through a separately licensed, checksum-bound channel and never
  overwrite it.
- Exact R0: 129 episodes, 31,366 frames, 59,904 windows, mixture
  `37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df`,
  statistics
  `02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae`,
  held-out rows excluded.
- Immutable diagnostics: F0 `807d3da7...`, F0a `278e8bc7...`, F0b result
  `8fb34ff4...`, and F0b replayable trace `af62a3b5...`.

## Frozen continuation and evaluation

- Fresh AdamW state; seed `20260801`; batch 8; MPS/fp32; policy and backbone
  learning rates `1e-5`; weight decay `1e-4`; gradient clip `10.0`; no
  scheduler; at most 2,000 optimizer updates.
- Evaluate chunk-50 only at continuation updates `0, 500, 1000, 2000`.
- Update 0 must reproduce the retained comparator before update 1.
- Episode 0 / seed 0; 244 frames; one queue reset; chunk starts
  `[0, 50, 100, 150, 200]`; executed lengths `[50, 50, 50, 50, 44]`; mask the
  six unexecuted terminal actions.
- Strict-v2 is the only verdict. Stop and preserve on the first Gate C pass;
  otherwise preserve update 2,000 as the terminal negative. No retry, sweep,
  threshold change, extra seed, or extra checkpoint.

## Day-one boundary

In the source repository, validate the package without loading the model:

```bash
external/lerobot/.venv/bin/python \
  scripts/robot_lab/write_f0c_release_targeted_package.py --check
external/lerobot/.venv/bin/python -m unittest \
  tests/unit/test_f0c_release_targeted_package.py
```

The fork must first implement and review the execution entrypoint, preserve it
on origin, and create fresh fork-native authority/proof artifacts. Only after
the fork's central composer mechanically opens its training lock may it run:

```bash
external/lerobot/.venv/bin/python \
  scripts/robot_lab/run_f0c_release_targeted_continuation.py \
  --spec configurations/robot_lab/f0c_release_targeted_continuation_spec.json \
  --started-at "$(date -Iseconds)"
```

That runner does not exist at the source-repo packaging boundary. Required
terminal evidence includes finite loss/gradient and sampler audits, full
decoded chunks, all 244 executed actions/observations, strict-v2 per-frame
margins, a signed MP4/manifest, content-addressed result/scorecard/retention/
final receipts, and independent reconstruction. A fork `RUN_RECEIPT.json`
never substitutes for these scientific artifacts and grants no hardware,
external-compute, transfer, or promotion authority.
