# Slice Brief 033 - Production Measured-Inertial Authority

**Date:** 2026-07-10

## Objective

Complete T16.4b by turning the truthful blocked real template and synthetic
compiler scaffold into a strict production measured-input compiler whose output
can earn only explicitly scoped downstream authority.

## Acceptance Criteria

- Add `scenesmith/robot_lab/artifact_contract.py` with strict JSON load,
  canonical finite JSON dump/hash, finite-number validation, unique-ID checks,
  signed payloads, and content-addressed artifact-reference verification.
- Reject `NaN`, positive/negative infinity, blank identifiers/provenance, duplicate
  measurement IDs, duplicate evidence identity, and non-content-addressed
  evidence.
- Validate prior/component/atom graph linkage and a hierarchical exact-cover BOM.
- Validate inertia tensors as symmetric positive semidefinite and enforce the
  rigid-body triangle inequality on principal moments.
- Support `cad_scaled`, `direct_inertia_tensor`, `primitive_geometry`,
  `point_mass`, `lumped_component`, and `measured_rigid_assembly` source modes.
- Require explicit mass/length/inertia/calibration units.
- Preserve full precision during component and assembly aggregation; round only
  the final serialized artifact.
- Replace `require_ready_or_raise` with explicit gates for compilation,
  simulation training, physical transfer, and promotion. Synthetic output may
  pass compilation only and must fail the latter three.
- Add a non-synthetic production fixture that ingests measured masses and mixed
  inertia source modes without hardware access.

## Validation

- Focused artifact-contract and measured-inertial unit tests.
- Adversarial duplicate-ID, cross-component prior, NaN/infinity, indefinite
  tensor, blank evidence, and synthetic-authority tests.
- Deterministic real measured-input happy path with golden aggregate values.
- Existing blocked real template and synthetic scaffold regressions.
- Broad twin/structural/measured-inertial artifact verification chain.

## Out Of Scope

- Physical measurements, hardware access, qualification status computation,
  T16.5 census work, optimizer runs, and unrelated dirty-worktree cleanup.

## Stop Conditions

- Stop if `status: ready` alone can authorize training or physical transfer.
- Stop if any production-ready measurement depends on a test-only synthetic
  marker or non-content-addressed evidence.
