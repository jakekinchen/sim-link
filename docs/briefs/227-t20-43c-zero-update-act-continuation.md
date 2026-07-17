# Slice Brief 227 - T20.43c Zero-Update ACT Continuation

**Date:** 2026-07-16

## Objective

Implement and fixture-test the smallest fail-closed recovery contract that can
answer ACT-on-R0 without rewriting T20.43b. Prefer an exact continuation from
the immutable checkpoint-0 boundary only if initialization, optimizer, sampler,
renderer, authority, and evidence equivalence are mechanically proven.

## Immutable source boundary

- T20.43b marker `d67cf38e...`, terminal receipt `89b6dbff...`, checkpoint-0
  identity `916200d0...`, model file `acc865fb...`, and chunk-50 trace
  `b707b815...` remain immutable.
- Recipe remains seed `20260801`, batch 8, AdamW `1e-5`/`1e-4`, 10,000 total
  updates, checkpoints `[0,500,1000,2500,5000,7500,10000]`, and strict-v2
  chunk-50/receding-10 evaluation on training episode 0.
- Dataset remains exact R0: 129 episodes, 31,366 frames, 59,904 windows, with
  held-outs excluded from training statistics.

## Implementation contract

- Use `render_rollout_mirror_v2.py` for actual-schema dispatch while retaining
  immutable legacy renderer bytes.
- Add separately named T20.43c owner/request/decision/runtime/permit,
  acceptance, continuation-marker, and final continuation-receipt artifacts.
- Require central `simulation_training_ready`; fail closed on any broader grant.
- Before the continuation marker, prove source commits, exact partial tree,
  actual-schema renderer smoke, sufficient disk, MPS/runtime/cache, path
  absence, and zero optimizer/sampler progress without loading model tensors.
- After the marker, prove checkpoint-0 tensor equality to fresh seeded ACT,
  empty optimizer state, and zero consumed training batches before update 1.
- Reuse the existing checkpoint-0 chunk-50 trace without rewriting it; render
  its missing mirror, execute checkpoint-0 receding-10, then updates 1-10,000
  and the remaining fixed evaluations.
- Bind the complete standard result to both the original attempt identity and
  the new continuation marker/permit through a signed outer receipt.

## Verification

- Deterministic tests for actual-schema dispatch, source/tree drift, coexisting
  output, tensor mismatch, nonempty optimizer, advanced sampler, authority
  escalation, stale origin, path aliasing, and receipt tampering.
- Focused T20.43b/T20.43c tests, T20.43/T20.44 regression, central composer and
  pointer checks, live actual-schema mirror smoke, offline lint/format,
  compilation, strict JSON, and whitespace.
- Fresh same-agent adversarial review before materialization and again before
  the continuation marker.

## Current authority

Reviewer 307 accepts the implementation and model-free fixture boundary after
57 selected tests and 15 subtests. Once that boundary is committed and exact on
origin, one actual-schema renderer smoke and compact model-free authority
materialization may run. The training lock remains closed. No continuation
marker, checkpoint tensor read, model construction/load/inference, optimizer,
training, rollout, Gate C execution, retry, fresh replacement, hardware,
network, external compute, Brev, transfer, promotion, or destructive operation
is authorized until a second review and signed acceptance are exact on origin.
