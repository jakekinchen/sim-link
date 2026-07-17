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

Reviewer 308 accepts the hardened implementation and model-free fixture
boundary after 70 selected regressions; Reviewer 307's separately recorded 15
subtests remain part of the initial review evidence. The terminal-failure path
now signs even when a consumed marker is followed by failure before the run
root contains its first file. Once that boundary is committed and exact on
origin, one actual-schema renderer smoke and compact model-free authority
materialization may run. The training lock remains closed. No continuation
marker, checkpoint tensor read, model construction/load/inference, optimizer,
training, rollout, Gate C execution, retry, fresh replacement, hardware,
network, external compute, Brev, transfer, promotion, or destructive operation
is authorized until a second review and signed acceptance are exact on origin.

Reviewer 309 additionally accepts one model-free administrative recovery after
the actual-schema smoke completed but dependency inventory received an
obsolete Python-3.11 MuJoCo path. No authority JSON or model action was written.
The recovery must reuse only the re-verified smoke MP4/manifest, record that
resume in the signed smoke receipt, and use the bound Python-3.12 support path.

That model-free recovery now verifies as smoke `9e8783dc...` and central
decision `c316bf01...`, granting only `simulation_training_ready` through permit
`166a6cd0...`. Training remains locked until the six-artifact bundle is exact
on origin and a separate reviewer decision plus signed acceptance are written
and preserved.

Reviewer 310 accepts origin authority commit `02496f0...`. Signed acceptance
`010d0a43...` binds that commit, permit `166a6cd0...`, and the reviewer file.
Once this acceptance boundary is exact on origin and the window is active, the
sole marker and post-marker equivalence gate may run once; update 1 remains
barred until equivalence passes.

## Terminal disposition

The sole marker was consumed. Equivalence passed exactly and the unchanged ACT
recipe reached optimizer update 728 with checkpoint-500 dual-cadence evidence.
A sibling thread then interrupted the process under a superseded scheduling
instruction. Reviewer 314 accepts terminal artifact `d848a1a8...` as an
inconclusive owner-directive interruption: not a trained negative, not an
infrastructure failure, not a Gate C pass, and not retry authority. Training
authority is closed and ACT-on-R0 remains unresolved.
