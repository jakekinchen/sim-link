# Slice Brief 024 - Truthful Measured Mass Intake And Inertia Compiler

**Date:** 2026-07-10

## Objective

Complete the offline T16.4 intake/compilation capability against the verified
T16.3 v2 baseline without inventing physical measurements. The checked-in real
arm remains blocked; a synthetic-only fixture proves ready-state inertia math.

## Current Truth

- No genuine physical piece-weight evidence exists in repo state.
- The seven explicit MJCF masses are CAD-derived priors, not measurements.
- Current-arm aggregate mass, COM, and inertia therefore remain unknown.
- Structural artifact identity is
  `fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9`.

## Required Real Artifacts

1. `configurations/robot_lab/pi05_measured_mass_intake.awaiting_measurements.json`
   with:
   - status `awaiting_measurements`;
   - an empty `measurements` collection;
   - stable component/assembly/frame and coverage-atom declarations;
   - explicit missing and unresolved inventory categories;
   - CAD priors in a separate namespace with origin `CAD`, never `measured`.
2. `configurations/robot_lab/pi05_assembly_inertials.blocked_missing_measurements.json`
   with:
   - status `blocked_missing_measurements`;
   - null or absent aggregate physical mass, COM, and inertia;
   - explicit missing coverage and rejected/unresolved evidence;
   - `physical_qualification_authority: false` and
     `training_or_promotion_authority: false`.

Both artifacts must be deterministic, schema-validated, content-addressed, and
bound by path, schema, file hash, and semantic identity to the current robotics
dependency lock, TwinProfile, structural diff, and (for output) intake.

## Intake And Coverage Contract

- Stable IDs describe component, assembly, canonical body/frame, category,
  installed state, evidence, `required_for_ready`, and explicit coverage atoms.
- Cover at least the known physical categories: printed/link structures,
  per-axis servos/actuators, horns/bearings, fasteners, wrist camera and mount,
  wiring/cable bundles, gripper fingertips/pads, and attachments/payloads.
- If repo evidence cannot prove the actual BOM or part count, record unresolved
  inventory rather than inventing it.
- A measurement declares an immutable ID, covered component/atom IDs, mass in
  kg, uncertainty, method/device/calibration provenance, evidence path/hash, and
  origin `measured`.
- A geometry prior declares source path/hash, source mass, source frame, COM,
  full inertia about COM, transform into assembly frame, units, origin, and
  assumptions.
- Selected measured coverage must be pairwise disjoint and cover every required
  atom exactly once before status can become `ready`. Reject parent/child
  overlap, duplicate evidence, multiple active measurements for one atom,
  ambiguous assembly membership, and exclusions used to hide required parts.

## Ready-State Math Contract

The compiler must support, and synthetic tests must prove:

- CAD inertia scaling by trusted measured mass only when source mass is valid.
- Rotation into the assembly frame: `R I_com R^T`.
- Parallel-axis translation:
  `m * ((d dot d) I3 - d d^T)`.
- Mass-weighted assembly COM and summed assembly inertia.
- Finite positive mass, valid transforms, symmetric positive-semidefinite
  inertia, and principal-moment triangle inequalities.
- Input-order invariance and deterministic serialized identity.

The ready proof fixture must be labeled `synthetic_test_only`, include multiple
components with nonzero translation and rotation, and never feed the default
production artifact.

## CLI Semantics

- Default write compiles the checked-in real intake and succeeds by emitting the
  truthful blocked artifact.
- `--verify` reproduces and verifies the checked-in artifacts.
- `--require-ready` exits nonzero while status is
  `blocked_missing_measurements`.
- Invalid, ambiguous, overlapping, stale, or tampered input hard-errors and must
  not overwrite the last valid artifact.

## Expected Files

- `scenesmith/robot_lab/measured_inertial_intake.py`
- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`
- The two real artifacts named above
- One executor session log and the task ledger

## Required Tests

- Empty real intake writes/verifies byte-stable blocked state with null physical
  aggregates; `--require-ready` rejects it.
- Complete synthetic fixture reaches `ready` and matches golden mass/COM/inertia
  values after nonzero rotation and translation.
- CAD-only values cannot satisfy measured coverage.
- Missing/unresolved inventory blocks without guessing.
- Duplicate, conflicting, overlapping, parent/child, and reused evidence fails.
- Invalid mass, transform, source mass, non-PSD inertia, and triangle-inequality
  violations fail.
- Tampered/stale dependency-lock, TwinProfile, structural-diff, intake, or
  evidence references fail.
- Component/input order does not change output or semantic identity.
- Focused tests, syntax compilation, live CLI write/verify, explicit
  `--require-ready` rejection, and the broad robot-lab suite all pass.

## Exit Condition

T16.4 is complete when the repo CLI truthfully generates and verifies the
blocked current-arm artifacts and the synthetic fixture proves the full ready
compiler. T16.5 may consume the blocker-aware contract offline. T19.5 and any
physical TwinProfile promotion must refuse the result until a future real intake
is `ready`. Do not claim M16 qualification or unlock training from this slice.
