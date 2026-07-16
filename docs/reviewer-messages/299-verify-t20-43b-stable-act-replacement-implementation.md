# Reviewer Decision 299 - Verify T20.43b Stable ACT Replacement Implementation

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43B_IMPLEMENTATION_FOR_MODEL_FREE_MATERIALIZATION_AFTER_ORIGIN`

The Brief 222 implementation is accepted for origin preservation. It defines
one task-specific ACT replacement while preserving the exact original recipe
and correcting only the renderer/runtime boundary that consumed T20.43 before
optimizer training.

## Verified implementation

- Spec `13c5bb4b2cadf8c451a25e7c11e9e0a1d824468f593774fdb60dbf7fa5197461`
  binds owner addendum `8b4a206`, synchronized T20.44 state `b24ac30`, original
  ACT spec `b3a510f8...`, original terminal receipt `b64ec6d0...`, T20.44
  terminal negative `9d916206...`, and stable smoke `11cbcca3...`.
- Campaign, ACT configuration, dataset, and evaluation objects equal the
  original signed T20.43 spec exactly: batch 8, seed `20260801`, AdamW
  `1e-5`/`1e-4`, no scheduler, 10,000 updates, checkpoints
  `[0,500,1000,2500,5000,7500,10000]`, and chunk-50/receding-10 strict-v2
  evaluation.
- Stable runtime is exact `external/lerobot/.venv/bin/python` plus the existing
  cached MuJoCo 3.3.5 support tree. Fresh smoke binds retained trace identity
  `6133ce58...` and exact trace-file SHA `f9dc0e6d...`, real renderer command,
  nonempty MP4/manifest, support-tree identity, and runner equality before the
  marker.
- Fresh Gate A, owner/composer/runtime/permit/acceptance/marker, complete
  rollout/mirror/result/scorecard/retention, generic post-marker terminal
  failure, and independent verification contracts use T20.43b-only paths.
- The generic failure path records current progress and partial-tree identity;
  it does not attempt to reproduce or relabel the retired missing-MuJoCo fault.

## Verification

- 11 focused T20.43b contract/runner tests pass.
- 30 T20.43/T20.44/T20.43b targeted and regression tests pass.
- 34 project-pointer, central-authority, and quantitative-receipt tests pass.
- Offline Ruff check and format check pass for all nine implementation/test
  files; Python compilation and all four CLI import/help probes pass.
- Strict spec reconstruction returns `13c5bb4b...`; whitespace and strict JSON
  checks pass.

## Adversarial findings

Temporary interpreter use, renderer failure, trace identity or byte drift,
support-tree mismatch, R0/source drift, recipe mutation, held-out leakage,
output alias/collision, stale authority, marker-order violation, non-finite
training, queue/tail error, strict-v2 spoofing, first-pass replacement, retry,
second replacement, correction objective, threshold change, and whole-system
authority escalation fail closed. The old T20.43 paths appear only as immutable
source evidence and smoke input; no old output can be overwritten.

## Authority granted

After this complete implementation boundary is committed, pushed, and exact on
`origin/codex/pi05-autolearn-loop`, materialize one fresh model-free Gate A,
real renderer smoke, owner/composer/runtime decision, and one-use permit for a
separate pre-run review.

## Authority withheld

No live materialization before origin, pre-run acceptance, marker, backbone or
model tensor read, model construction/load/inference, optimizer creation or
training, checkpoint, rollout, Gate C/D/E claim, retry, second replacement,
archive replay, T20.45, hardware/camera/serial access, physical motion,
network/package installation, external compute, Brev, transfer, promotion, or
destructive operation.
