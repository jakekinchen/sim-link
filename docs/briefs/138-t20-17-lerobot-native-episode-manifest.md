# Slice Brief 138 - T20.17 LeRobot-Native Episode Manifest

**Date:** 2026-07-14

## Objective

Replace the parallel dataset's first responsibility—episode provenance and
eligibility—with a small signed view over one actual `LeRobotDataset`. The view
must not materialize frames, segments, windows, or a replacement Parquet store.

## Contract

- Require the pinned `LeRobotDataset` object at the boundary and derive counts,
  metadata identity, and per-episode content hashes directly from it.
- Bind every episode to one content-addressed raw-rollout identity plus an
  explicit `eligible` or `quarantined` status/reason. Missing, duplicate, or
  out-of-range episode annotation fails closed.
- Hash only metadata and the package's actual episode samples; do not create,
  translate, or mutate dataset rows, Parquet files, frame tables, segment
  tables, windows, buffers, statistics, or source evidence.
- Keep the manifest local-capability-only. It grants no training, model,
  simulator, hardware, physical-transfer, promotion, external-compute, or Brev
  authority.

## Acceptance Criteria

- A real temporary `LeRobotDataset` produced by the pinned package can build
  and verify an identical signed manifest on repeated reads.
- Changing a sourced episode, provenance identity, eligibility, quarantine
  reason, metadata file, or episode mapping fails verification.
- The contract reports zero new storage rows and no normalization or pipeline
  logic; actual PI0.5 pipeline output hashing is a separate next slice.

## Out Of Scope

Persistent dataset creation, raw rollout conversion, optimizer/model execution,
Pi0.5 processor invocation, live-observation changes, hardware, external
compute, and Brev.
