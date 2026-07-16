# Slice Brief 220 - T20.44 R2 SmolVLA Standard Rung

**Date:** 2026-07-16

## Objective

Implement and fixture-test the exact R0 Gate A parity, cached-base SmolVLA
standard fine-tuning recipe, fixed checkpoint/evaluation schedule, real child-
interpreter renderer smoke, complete strict-v2 trace/video evidence, central
authority, runtime preflight, one-use permit, immutable failure handling, and
result contracts for one bounded local-MPS R2 attempt. Commit, push, and review
that implementation before materializing any live preflight or loading model
weights.

## Frozen source boundary

- Bind T20.43 terminal commit `2e6a3e34406e0b251b9af4b7a6b83100e18af785`,
  Reviewer 293, attempt `064e5650...`, and terminal receipt `b64ec6d0...`.
  T20.43 cannot retry and supplies no trained ACT capability result.
- Bind R0 result `d238379b...`, mixture `37b30d34...`, statistics
  `02ba0e70...`, retention `19d19fba...`, and package manifest `bd36b7c4...`.
  Load exactly 129 episodes and 31,366 frames; held-out seeds 6-7 and the nine
  fresh-held-out R0 candidates remain outside training and fitted statistics.
- Bind the verified T20.36i/j SmolVLA dependency closure, corrected processor
  smoke, cache/tree evidence, and the prior 2,000-update result only as runtime,
  cache, trainable-scope, and fault-localization evidence. The old ten-episode
  fixed-batch objective, old checkpoint, Gate B decision, and old normalization
  statistics are not training inputs and cannot select this result.
- Bind LeRobot commit `e40b58a8...`, the exact SmolVLA/config/processor/
  dataset/optimizer/scheduler source files used, policy snapshot revision
  `c83c3163...`, and VLM snapshot revision `7b375e1b...`. Hash every file in
  both loaded snapshot trees without network fallback.

## Exact standard recipe

- Start from the exact cached `lerobot/smolvla_base` policy and its pinned
  SmolVLM2-500M VLM. Do not load the retained T20.36j fine-tuned checkpoint.
- Preserve the validated feasible trainable scope: frozen vision encoder,
  `train_expert_only=true`, `train_state_proj=true`, no PEFT, and no full-VLM
  training. Runtime inventory must prove every and only intended trainable
  parameter and all parameters/buffers on MPS.
- Use two real dataset camera inputs, six state/action dimensions, one
  observation, chunk 50, training `n_action_steps=50`, visual IDENTITY and
  R0 training-only state/action MEAN_STD, tokenizer length 48, ten flow steps,
  cross attention, and no compilation or mixed precision.
- Use LeRobot's official SmolVLA presets: batch size 8, AdamW learning rate
  `1e-4`, betas `(0.9,0.95)`, epsilon `1e-8`, weight decay `1e-10`, gradient
  clipping 10.0, and cosine decay with 1,000 warmup steps, 30,000 decay steps,
  and `2.5e-6` floor. Seed all Python/NumPy/Torch/sampler streams with
  `20260831`. Shuffle full R0 windows; no fixed-batch repetition, oversampling,
  correction objective, sample weighting, held-out ingestion, or sweep.
- Run exactly 5,000 maximum optimizer updates with scheduled checkpoints
  `[0,500,1000,2500,5000]`. Continue the sole run through 5,000 finite updates
  even if a checkpoint passes; freeze the first valid Gate C evidence as soon
  as it appears.

## Gate A and rollout-primary evaluation

- Before model weights, reconstruct R0 package/tree/count/order/features,
  training-only statistics, fixed sample tensors, SmolVLA processor shapes and
  tokens, action inverse, and dataset-to-MuJoCo coordinate round trip. Missing,
  non-finite, reordered, held-out-contaminated, or mismatched evidence fails
  before the marker.
- Gate A is parity evidence only. No one-batch/open-loop threshold may block a
  safe simulation rollout.
- At every checkpoint, run unchanged nominal training episode 0 for 244 frames
  under chunk-50 starts `[0,50,100,150,200]` with executed lengths
  `[50,50,50,50,44]`, and receding-10 starts `[0,10,...,230,240]` with 24
  tens plus a final four. Reset the queue once per rollout and exclude every
  unexecuted tail action.
- Strict-v2 is the only success oracle. The first scheduled checkpoint passing
  either variant is Gate C; chunk-50 wins a same-checkpoint tie. Retain complete
  proposed/applied/state/object/contact traces, first divergence, strict-v2
  and T20.38 margins, report-only amended/uniform analyses, decode hashes,
  source identities, and signed MP4 manifests.

## Mandatory renderer/dependency correction

- Before any new attempt marker, execute the real
  `scripts/robot_lab/render_rollout_mirror.py` entrypoint with the exact Python
  interpreter/environment that the R2 runner will use. Render retained trace
  `6133ce58...` to a dedicated T20.44 smoke path, require process exit 0,
  nonempty MP4, valid signed manifest, matching trace/output hashes, and
  MuJoCo 3.3.5. Bind interpreter path, version, dependency inventory, command,
  stdout/stderr hashes, output identity, and tree into preflight.
- The smoke is model-free support evidence and cannot grant training. Any
  child/parent interpreter mismatch, missing dependency, fallback, alias, or
  output collision fails before the marker. The training runner must reuse
  this exact interpreter invocation; it may not hardcode another venv.
- Recursively verify the already-installed SmolVLA optional-dependency closure
  and exact offline AutoProcessor smoke before model weights. No package
  installation or environment mutation is authorized by this brief.

## Authority and one-attempt boundary

- Implement task-specific owner, central request/decision, live preflight,
  one-use permit, signed acceptance, marker-first runner, full verifier,
  terminal-success/negative result, and signed runtime-failure evidence.
- Implementation must be committed, pushed, and reviewed before materializing
  Gate A, renderer smoke, authority, or permit. Those materialized artifacts
  must then be committed, pushed, and separately accepted before the marker.
- The marker follows the complete renderer/dependency smoke and precedes policy
  or VLM weight reads, SmolVLA construction, inference, and optimizer creation.
  Once written, it consumes the sole R2 attempt. Any later failure is retained
  and terminal; no retry or replacement is implied.
- Checkpoint/rollout/video trees remain local with signed identities. Compact
  specs, decisions, results, scorecards, manifests, and terminal receipts are
  tracked.

## Verification

- Tests first cover source/cache/dependency/snapshot/dataset/statistics/held-out
  drift, incorrect trainable scope, unsafe config/defaults, scheduler or batch
  mutation, renderer child mismatch, smoke omission/failure/spoofing, output
  aliases, stale authority, marker ordering, non-finite loss/gradient, missing
  checkpoints, queue/tail errors, strict-v2 spoofing, first-pass replacement,
  trace/video drift, retry, and prohibited authority fields.
- Run focused SmolVLA tests, relevant dataset/closed-loop/strict-v2/receipt/
  renderer regressions, Ruff, compilation, strict JSON, project-pointer,
  scoped-diff, remote-preservation, and fresh same-agent adversarial reviews.

## Authority withheld

This brief opens implementation and fixture tests only. No live Gate A,
renderer smoke, authority artifact, attempt marker, policy/VLM weight read,
SmolVLA construction/load/inference, optimizer creation/training, checkpoint,
learned rollout, Gate C/D/E claim, retry, replacement, correction objective,
Gate B entry barrier, threshold change, archive replay, T20.45 activation,
hardware/camera/serial access, physical motion, network/download, package
installation, external compute, Brev, physical transfer, promotion, or
destructive operation.
