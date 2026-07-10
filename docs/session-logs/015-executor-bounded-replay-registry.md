# Executor Session 015 - Bounded Replay Registry

**Date:** 2026-07-10

## Slice

Complete T11.4 and M11 with a cumulative correction registry that retains prior
accepted sources under explicit source/frame budgets and refuses drift.

## Result

- Registry entries bind dataset contract, info metadata, and correction sidecar
  hashes to cycle IDs and monotonic sequence numbers.
- Oldest sources are evicted only when configured source/frame bounds require it.
- Every registry load verifies files; missing or mutated artifacts fail closed.
- Overlapping `(scene, seed, frame)` identities are rejected to prevent duplicate
  trajectories from silently receiving extra replay weight.
- Merge accepts a verified registry, combines all disjoint correction datasets,
  emits a consolidated replay sidecar, and preserves the accepted normalizer.
- The cycle now updates the registry before merge and plans replay from the
  consolidated sidecar.

## Verification

- 57 intervention/autolearn tests pass.
- Synthetic registry tests retain history, enforce bounds, reject mutation, and
  reject overlapping correction identities.
- A real attempt to register M10 and M11 exports of the same seed-6204 trajectory
  was correctly rejected as overlap rather than double-counted.
- A clean registry containing the 870-frame M11 context dataset merged into a
  12-episode/11,526-frame training dataset with pinned normalization.

## Proof Boundary

Only one real disjoint correction collection currently exists. The multi-cycle
retention mechanism is proven structurally; future cycles must use disjoint
training seeds before the registry can accumulate multiple real entries.

## Next Step

T12.1 stage-level evaluation metrics.
