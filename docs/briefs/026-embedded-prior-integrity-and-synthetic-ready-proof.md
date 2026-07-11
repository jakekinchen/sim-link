# Slice Brief 026 - Embedded Prior Integrity And Synthetic Ready Proof

**Date:** 2026-07-10

## Objective

Finish T16.4 by closing the nested-evidence integrity gap in the blocked real
intake and then proving the complete ready-state compiler with a strictly
synthetic fixture. The default real arm remains blocked and unqualified.

## Part A - Strengthen The Existing Blocked Baseline

- The checked-in `awaiting_measurements` intake must match a deterministic
  normalized rebuild from the pinned runtime MJCF, dependency lock, TwinProfile,
  and structural diff—not merely carry a valid self-signature.
- Re-signed changes to any embedded CAD-prior source path/hash/size, source mass,
  source COM/inertia, body-to-assembly transform, units, origin, or assumptions
  must fail verification.
- Duplicate component IDs, atom IDs, prior IDs, or inconsistent component/atom/
  prior links must fail.
- `build_assembly_inertials` must consume only an intake that passes this full
  verification, so a forged CAD prior cannot alter even a diagnostic summary.
- Preserve the current checked-in blocked artifact contents and identities if
  the stronger verifier does not require a schema/content change.

Required direct regression: a re-signed intake with one source mass changed to
`99` kg must fail, and no compiled output may be written from it.

## Part B - Synthetic Ready Compiler

- Add a fixture under
  `tests/fixtures/robot_lab/measured_mass/synthetic_complete.json`, explicitly
  labeled `synthetic_test_only` and unreachable as the default production input.
- Support a complete measured intake with stable measurement/component/atom/
  assembly/frame IDs, immutable evidence refs, uncertainty, method/device/
  calibration provenance, and origin exactly `measured`.
- Select measurements only when required coverage atoms form one pairwise-
  disjoint exact cover. Reject missing atoms, duplicate active coverage,
  parent/child overlap, reused evidence, ambiguous assembly/frame mapping, or
  exclusions that hide required material.
- CAD-origin entries can supply geometry/inertia priors but never measured mass
  coverage.

For each selected component:

1. Scale the prior inertia about component COM by measured/source mass.
2. Rotate it into the assembly frame with `R I_com R^T`.
3. Transform component COM into the assembly frame.
4. Compute mass-weighted aggregate COM.
5. Sum rotated inertias plus
   `m * ((d dot d) I3 - d d^T)` about the aggregate COM.

Validate finite positive measured/source masses, finite orthonormal proper
rotation matrices, finite transforms, symmetric positive-semidefinite inertia,
and principal-moment triangle inequalities. Reject invalid inputs; never repair
them silently.

## Determinism And Separation

- Component, prior, and measurement input ordering must not change the ready
  artifact or semantic identity.
- The synthetic fixture must include multiple components, nonzero translations,
  and a non-identity rotation with independently calculated golden mass, COM,
  and full inertia.
- The synthetic path may use a bounded explicit CLI option or a test-facing API,
  but it must refuse to write to either default real-artifact path.
- Default write/verify continues to reproduce the real blocked artifacts;
  default `--require-ready` continues to exit nonzero.

## Negative Test Matrix

- Re-signed embedded real-prior path/hash/mass/COM/inertia/transform tampering.
- Duplicate component and atom/prior IDs.
- CAD-only pseudo-measurement.
- Missing, duplicate, overlapping, parent/child, and reused-evidence coverage.
- Invalid measurement/source mass or uncertainty/provenance.
- Invalid transform shape, non-orthonormal/reflected rotation, nonfinite values.
- Nonsymmetric, non-PSD, or triangle-inequality-invalid inertia.
- Stale/tampered dependency-lock, TwinProfile, structural-diff, intake, and
  evidence refs.
- Input-order invariance and repeated-build byte/identity equality.

## Validation

- `python -m unittest tests.unit.test_measured_inertial_intake`
- Syntax-compile the module, tests, and CLI.
- Default CLI write and verify succeed on the blocked real artifacts.
- Default CLI `--verify --require-ready` fails nonzero with the declared blocked
  status.
- Run the bounded synthetic ready demo and record its golden outputs/identity.
- Run the broader dependency-lock, twin-contract, structural-diff, and measured-
  inertial suite.

## Exit Condition

T16.4 closes only when both Part A and Part B pass fresh independent review. The
real arm remains `blocked_missing_measurements`; the synthetic fixture proves
compiler capability only. No physical qualification, training, or M17 work is
authorized by this slice.
