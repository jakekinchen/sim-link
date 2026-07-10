# Executor Session 019 - Runtime Provenance

**Date:** 2026-07-10

## Slice

Complete T12.4 by content-addressing the executable LeRobot/PI0.5 runtime,
preprocessing, model, dataset, replay, normalizer, and checkpoint surfaces.

## Result

- Provenance records the resolved Python executable/version/platform, package
  versions, torch MPS build/availability, and hashes of training/configuration/
  PI0.5 modeling/processor/sample-weighting sources.
- Every file in the model tree is hashed; a canonical tree digest binds names,
  sizes, and content.
- Runtime, training-input, and finalized-candidate provenance stages bracket the
  cycle's evaluation/training boundaries.
- Training provenance includes dataset contract, merge summary, pinned stats,
  consolidated sidecar, replay plan, replay registry, and seed registry.
- Resume now compares current artifact hashes to recorded stage evidence instead
  of accepting mere path existence.

## Verification

- 64 intervention/autolearn tests pass, including artifact mutation and resume drift.
- Real accepted-checkpoint canary hashed nine files/92,383,464 bytes with tree
  SHA-256 `348262827c8a83cfb317c841f77795e3779bf52078530f808a71cb2a608afd43`.
- Runtime identity is `29917c59e1067cb1564df640377d3f34ebe7bf7d9956c19e0913cb2ebfc76802`.
- Manifest verification reread all sources, artifacts, and model files successfully.

## Proof Boundary

The provenance manifest describes this exact Mac runtime; it intentionally fails
on a different or mutated environment until a new reviewed identity is recorded.

## Next Step

T12.5 bounded evaluation I/O and persistent policy services.
