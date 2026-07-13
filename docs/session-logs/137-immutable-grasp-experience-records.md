# Session 137 - Immutable Grasp Experience Records

**Date:** 2026-07-13

Brief 107 establishes the first M17 raw-rollout/frame-record contract. It binds
the verified geometry-derived grasp, simulation twin, and coordinate identities;
defines stable rollout/frame IDs, integer nanosecond time, prompt identity,
orthogonal source/proof/phase/mode/owner dictionaries, five distinct action
variants, sourced gripper/contact/aperture/effort fields, reward/progress
provenance, hard boundaries, and actor-privilege exclusions.

The two-frame source projection preserves MuJoCo source phases separately from
canonical task phases. `recovery` is a control mode and cannot be a task phase.
Because T19.0l does not retain per-frame actions, requested/achieved gripper
poses, or effort—and because segments, windows, and normalization do not yet
exist—the fixture carries five quarantine reasons and is not training eligible.

Artifact `f2b8b462...` verifies with file SHA-256 `4214679b...`. Twelve focused
tests pass in each configured runtime and the 210-test broad gate passes. No
Parquet table, compiled training frame, hardware access, optimizer, training,
Brev, paid compute, or physical motion occurred. The training lock remains
closed.
