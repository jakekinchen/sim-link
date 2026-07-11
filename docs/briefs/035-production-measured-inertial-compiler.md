# Slice Brief 035 - Production Measured-Inertial Compiler

**Date:** 2026-07-11

## Objective

Complete the remaining structural, source-mode, metrology, unit-conversion, and
full-precision aggregation path for T16.4b without weakening the verified
Brief 034 authority boundary. Add one deterministic production-schema fixture
that executes the same compiler used for future measured inputs while remaining
explicitly fixture evidence.

## Contract

- Keep the checked-in current-arm intake and assembly artifact blocked until
  real measurements exist.
- Add a versioned production intake schema with one rooted hierarchical acyclic
  BOM. Every non-root component has exactly one parent and one transform edge;
  frame IDs are unique and every selected component has exactly one path to the
  assembly target frame.
- Derive required-leaf coverage from the BOM. Selected measurements must form
  an exact cover. Selecting an ancestor and descendant together is invalid.
- Support exactly `cad_scaled`, `direct_inertia_tensor`,
  `primitive_geometry`, `point_mass`, `lumped_component`, and
  `measured_rigid_assembly`.
- Treat scale evidence as mass-only. Each mode declares and validates separate
  mass, center-of-mass, and inertia derivations.
- Require explicit native and canonical mass/length/inertia units, deterministic
  SI conversion, device and calibration identities, content-addressed evidence,
  raw values, repeatability, resolution, uncertainty, inherited assumptions,
  and approximation/CAD uncertainty.
- Preserve unrounded finite internal values through frame transforms and
  parallel-axis aggregation. Round only serialized result fields.
- Emit assembly-inertials v2 local capabilities only. Fixture output must carry
  `qualification_scope=fixture_evidence` and
  `physical_measurement_evidence_verified=false`.

## Fixture and adversarial matrix

The production fixture must exercise all six source modes and include a parent
rigid-assembly measurement covering multiple required leaves. Tests must cover:

- golden aggregate mass, center of mass, and inertia;
- input-list order invariance;
- missing and overlapping leaf coverage;
- selected ancestor/descendant conflict;
- missing/unknown parents, multiple roots, cycles, duplicate frame IDs, and
  disconnected or ambiguous transform paths;
- wrong or implicit units and conversion drift;
- blank device/calibration identity;
- scale evidence falsely claiming COM or inertia;
- missing metrology/uncertainty/assumptions;
- evidence reuse/substitution and non-finite raw/intermediate/output values;
- forged component global-authority fields; and
- refusal to write fixture output over either checked-in current-arm artifact.

## Validation

- Focused production-compiler and existing measured-inertial tests.
- Live fixture CLI write and verify through
  `scripts/robot_lab/write_measured_inertial_intake.py`.
- Existing blocked current-arm write/verify path.
- Authority-composer denial path for the fixture output.
- `py_compile` and `git diff --check`.

## Out of scope

Numerical eigensolver convergence/residual hardening is the immediately
following T16.4b sub-slice. No live hardware, physical measurements,
qualification metric computation, optimizer work, transfer, deployment, or
promotion is authorized.

## Authority after this slice

This slice may establish only the production measured-inertial compiler
capability on fixture evidence. It grants no global decision, physical
measurement evidence, physical qualification, transfer, deployment, promotion,
or optimizer authority. `training_lock` remains closed.
