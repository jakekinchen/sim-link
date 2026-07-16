# Reviewer Decision 291 - Verify T20.43 R1 ACT Standard Implementation

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43_IMPLEMENTATION_AUTHORIZE_GATE_A_AUTHORITY_MATERIALIZATION_ONLY`

## Findings

- Spec `b3a510f8...` fixes one full, fresh ACT policy with the official cached
  ImageNet ResNet-18 initialization, full 512/8/3200/four-layer VAE recipe,
  batch 8, 10,000 AdamW updates, and seven immutable checkpoint boundaries.
  It cannot silently fall back to the earlier tiny ACT control.
- Gate A is model-free and reconstructs the exact R0 package/tree/count/feature/
  statistics boundary. Processor/manual MEAN_STD, action inverse, and physical
  coordinate round trips are independently checked before a marker.
- Authority composition grants only central `simulation_training_ready` and a
  single task permit. Exact dependency versions, cached backbone bytes, MPS,
  origin ancestry, scoped dirt, disk, output absence, and reviewer bytes all
  fail closed.
- The marker precedes cached backbone deserialization, model construction,
  inference, and optimizer creation. It consumes the sole attempt; retry,
  resampling, correction objectives, threshold changes, network, external
  compute, and R2 remain false.
- Every scheduled checkpoint evaluates both queue contracts. Decode starts and
  executed lengths are exact, final tails are excluded, strict-v2 is the only
  oracle, and amended/uniform action metrics remain report-only.
- Complete traces link requested/applied actions, state, anchor/contact state,
  strict-v2 margins, T20.38-compatible quantitative margins, checkpoint/source
  identities, and mirror bytes. The earliest Gate C pass is immutable and
  later checkpoints cannot replace it.

## Adversarial review

- Source/cache/dependency/feature/order/statistics/held-out drift, path aliases,
  dirty authority/reviewer artifacts, stale time, schedule mutation, unsafe
  ACT defaults, non-finite optimization, missing/duplicate checkpoints,
  queue-reset/tail errors, strict-v2 spoofing, source substitution, trace/video
  mismatch, first-pass replacement, retry, and authority escalation fail.
- Evaluation no longer reseeds the global training stream; the official seeded
  sampler/VAE RNG sequence continues across fixed probes.
- The local LeRobot checkout has unrelated PI0.5/train-script dirt, but the R1
  runner imports and hashes only its explicit ACT/dataset/optimizer surfaces;
  those paths are source-bound and the unrelated dirt remains untouched.
- The AV/cv2 duplicate-class message observed while reading the image dataset
  is a runtime warning, not a fallback or failed Gate A check. No video/model
  action occurred during the probe.

## Verification

- 9 focused T20.43 tests pass.
- 75 focused-plus-broad regressions pass.
- Model-free Gate A `90217d2b...` and the prospective central/permit bundle
  reconstruct from real sources.
- Ruff check/format, Python compilation, strict JSON, spec reconstruction, and
  whitespace checks pass.

## Disposition

Commit and push this complete implementation/spec/review boundary. Once its
commit is exact on origin and the owner window remains active, materialize only
the six compact Gate A/owner/request/decision/runtime/permit artifacts. Commit
and push them, then perform a separate Reviewer 292 pre-run reconstruction and
signed acceptance before creating the marker.

## Authority withheld

No live Gate A/authority materialization before origin preservation; no pre-run
acceptance, attempt marker, backbone tensor read, model construction/load,
inference, optimizer creation/training, checkpoint, learned rollout, Gate C/D/E
claim, retry, correction objective, Gate B entry barrier, threshold change,
archive replay, hardware/camera/serial access, physical motion, network,
external compute, Brev, physical transfer, promotion, destructive operation,
or R2 activation.
