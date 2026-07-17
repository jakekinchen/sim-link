# Slice Brief 229 - T20.43c Manual Replacement

**Date:** 2026-07-16

## Objective

Close W0 with one complete ACT-on-R0 result while preserving the consumed first
T20.43c continuation exactly. Because optimizer state at update 728 was not
retained, do not claim an exact resume. Use one separately rooted manual
replacement only after a new fail-closed authority chain and completion-budget
check.

## Immutable interruption boundary

- First continuation marker `e086c293...`, equivalence `85087b2a...`, terminal
  interruption `d848a1a8...`, and partial-tree identity `e0aea95f...` remain
  immutable.
- The interruption occurred at optimizer update 728 after equivalence passed.
  No optimizer state exists from which an honest exact resume can occur.
- The original T20.43b checkpoint-0 model remains the fixed start:
  `916200d0...` / model file `acc865fb...`.

## Replacement contract

- New task/evidence label `T20.43c-R2`; disjoint authority, marker, result, and
  run-root paths; replacement ordinal 2, attempt count 1.
- Same seed `20260801`, batch 8, AdamW `1e-5` / `1e-4`, 10,000 updates,
  checkpoints `[0,500,1000,2500,5000,7500,10000]`, R0 dataset, strict-v2
  oracle, and chunk-50/receding-10 rollout evaluation.
- Marker precedes model/checkpoint/optimizer work. Update 1 remains barred until
  fresh seeded ACT tensors are bit-exact to checkpoint 0, AdamW is empty, and
  the sampler has consumed zero batches.
- Require at least four hours remaining in the finite authority window before
  the marker. Any post-marker exception or keyboard interruption writes a
  terminal receipt and authorizes no further retry.
- Central composer may grant only `simulation_training_ready`. Every hardware,
  network, external/Brev, transfer, and promotion surface remains false.

## Verification

- Deterministic tests for single-attempt owner scope, disjoint paths, closed
  acceptance/marker linkage, exact equivalence, completion-budget failure,
  terminal-tree binding, retry denial, and scoped runner adaptation.
- Focused T20.43b/T20.43c/T20.43c-R2 tests plus authority-composer, pointer,
  JSON, compilation, Ruff, and whitespace checks.
- Same-agent adversarial review before model-free materialization and again
  before acceptance/marker.
- Authority commit and acceptance commit must each be exact on origin before
  the next irreversible boundary.

## Current authority

Implementation and model-free fixture tests only. The training lock remains
closed. No new owner/request/decision/runtime/permit, acceptance, marker,
checkpoint read, model construction, optimizer, rollout, Gate C action,
hardware, network, external compute, Brev, transfer, or promotion is authorized
until review and remote preservation make each prerequisite exact.
