# Reviewer Decision 294 - Verify T20.44 R2 SmolVLA Standard Implementation

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_44_IMPLEMENTATION_AUTHORIZE_GATE_A_RENDERER_AUTHORITY_MATERIALIZATION_ONLY`

## Findings

- Spec `0cc8dcaa...` binds exact R0, the pinned `smolvla_base` policy and
  SmolVLM2 snapshots, verified dependency closure, two real cameras, the
  validated expert-plus-state-projection trainable scope, batch 8, 5,000
  updates, and checkpoints `[0,500,1000,2500,5000]`.
- AdamW and cosine scheduling use the policy's official presets. The declared
  1,000/30,000 warmup/decay settings officially auto-scale to 166/5,000 for
  this bounded run; every realized learning rate is retained.
- Gate A is model-free and reconstructs package/order/count/features,
  training-only R0 statistics, SmolVLA processor image/state/action/token
  behavior, postprocessor inverse, held-out exclusion, and coordinate parity.
- The corrected preflight invokes the real mirror-renderer entrypoint with
  `sys.executable`, requires MuJoCo 3.3.5, exact retained trace `6133ce58...`,
  exit 0, a nonempty MP4, and a signed content-addressed manifest. Runtime and
  runner reject an interpreter mismatch.
- The marker follows the complete dependency/processor/renderer preflight and
  precedes policy/VLM weight reads, model construction, inference, and
  optimizer creation. Any exception after it writes a signed terminal receipt
  from an atomically maintained progress state and cannot authorize retry.
- Both queue variants run at every checkpoint. SmolVLA noise is generated from
  pre-registered per-decode CPU seeds and hashed before transfer to MPS without
  reseeding or consuming the training RNG stream. Strict-v2 remains the sole
  oracle; amended and uniform metrics remain report-only.

## Adversarial review

- Source, snapshot, dependency, R0 statistics, held-out, trainable-scope,
  device, scheduler, batch, renderer interpreter/output, authority, output
  alias, checkpoint schedule, decode seed, queue/tail, strict-v2, trace/video,
  first-pass, retry, and terminal-failure drift fail closed.
- `PYTORCH_ENABLE_MPS_FALLBACK=0`; every trainable pathway and all model
  parameters/buffers must remain on MPS.
- The old T20.36j fine-tuned checkpoint, its fixed batch, old normalization,
  and Gate B result are evidence only and cannot initialize or select R2.
- T20.43 remains consumed and cannot be revived by the renderer correction.

## Verification

- 10 focused T20.44 tests pass.
- 80 focused-plus-broad tests and 30 subtests pass.
- Ruff check/format, Python compilation, strict JSON/spec reconstruction,
  project-pointer checks, and whitespace checks pass.
- No live renderer smoke, processor smoke, policy/VLM tensor read, model,
  inference, optimizer, checkpoint, or rollout action occurred.

## Disposition

Commit and push the complete implementation/spec/review boundary. Once exact
on origin and the owner window remains active, materialize only the model-free
Gate A, exact-interpreter renderer smoke, owner/request/decision/runtime, and
one-use permit artifacts. Commit and push them, then perform a separate
Reviewer 295 pre-run reconstruction and signed acceptance before the marker.

## Authority withheld

No live materialization before origin preservation; no acceptance, marker,
policy/VLM weight read, model construction/load/inference, optimizer creation/
training, checkpoint, learned rollout, Gate C/D/E claim, retry, replacement,
correction objective, Gate B barrier, threshold change, archive replay,
T20.45, package install, hardware/camera/serial access, physical motion,
network/download, external compute, Brev, transfer, promotion, or destructive
operation.
