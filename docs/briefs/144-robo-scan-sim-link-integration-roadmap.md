# Slice Brief 144 - Robo Scan And Sim-Link Integration Roadmap

**Date:** 2026-07-14

## Objective

Turn the foundry proposal and both repositories' current states into one exact,
gate-driven cross-repository integration and deduplication roadmap. Preserve
Robo Scan's active Brief 054 worktree and define what each project owns, how
artifacts cross the boundary, when a live integration becomes eligible, and
which duplicate sim-link surfaces may eventually retire.

## Contract

- Do not merge Git histories, vendor private implementations, or read from a
  mutable sibling checkout at runtime.
- Robo Scan remains the producer of capture, metric scene, calibration, and
  source-local evidence. Sim-link remains the consumer/compiler for MuJoCo,
  task/episode generation, LeRobot data and policy work, strict evaluation,
  and central authority composition.
- Use Robo Scan's immutable source-free export receipt as the first handshake.
  A sim-link adapter begins only after that producer boundary is committed and
  independently reopenable.
- Deduplicate only after feature parity, call-site migration, adversarial
  compatibility tests, and at least two verified handoffs. Preserve historical
  evidence and independent producer/consumer verification.
- Keep reference-only, metric-candidate, calibrated-twin, training-ready,
  physical-transfer, and promotion states mechanically distinct.

## Acceptance Criteria

- The roadmap names repository ownership, shared contracts, artifact flow,
  compatibility/versioning rules, phase gates, concrete implementation slices,
  rollback conditions, and the deduplication disposition of overlapping code.
- It explicitly reviews Robo Scan Brief 054 as the producer-side starting gate
  without editing the dirty Robo Scan worktree.
- The documentation hub, architecture boundary, decisions index, and document
  map route to the roadmap.
- Static documentation tests and project-state pointer checks pass; the scoped
  documentation boundary is reviewed, committed, and preserved on the allowed
  remote branch.

## Out Of Scope

Editing Robo Scan, implementing an importer, consuming an export, changing a
scene, modifying calibration, deleting duplicate code, opening hardware,
training, external compute, Brev, merging repositories, or granting any twin,
transfer, policy, or promotion authority.
