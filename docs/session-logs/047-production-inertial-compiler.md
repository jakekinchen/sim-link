# Session 047 - Production Measured-Inertial Compiler

**Date:** 2026-07-11

## Scope

Execute Brief 035 as the main remaining T16.4b production compiler sub-slice.
No hardware, optimizer, paid compute, or physical evidence was used.

## Implementation

- Added a rooted hierarchical BOM with one parent and one transform edge per
  non-root component, unique frames, cycle/disconnection rejection, and derived
  required-leaf exact cover.
- Added `cad_scaled`, `direct_inertia_tensor`, `primitive_geometry`,
  `point_mass`, `lumped_component`, and `measured_rigid_assembly` through one
  production-schema compiler.
- Bound native and canonical units, SI conversions, raw values, device and
  calibration identities, repeatability, resolution, uncertainty, inherited
  assumptions, approximation uncertainty, and content-addressed evidence.
- Preserved unrounded finite internal values through transforms and
  parallel-axis aggregation; rounding occurs only in serialized output.
- Added a deterministic fixture-evidence input/output pair covering all six
  modes and a parent assembly covering two leaves. The same schema also accepts
  content-addressed physical inputs as local inertial evidence without global
  authority.
- Kept the checked-in current-arm artifact blocked and prevented fixture or
  custom production inputs from overwriting its checked-in destinations.

## Evidence

- Implementation commit: `a93ff057f8cf4f966d4edc8dc0098c3526a14def`.
- Fixture intake identity:
  `fe9dbd5468a606019db735dc8664c05d5fc207d94bdcbc84243f58cfa98f869f`.
- Fixture output identity:
  `b8d7c5d287051aa863c3ef08597deefb9dd7685ad2c89d820456f92491fef25d`.
- Golden aggregate: mass `3.2 kg`, COM `[0.016875, 0.4184375, 0.0] m`,
  inertia `[[0.418985520833, 0.051635625, 0.0], [0.051635625,
  0.020303194444, 0.0], [0.0, 0.0, 0.437746493056]] kg*m^2`.
- Focused production suite: 21 tests passed in 23.172 seconds.
- Broad feeding/consuming gate: 122 tests passed in 71.332 seconds.
- Fixture, integrated measured-inertial, current blocked-arm, default composer,
  and fixture-composer product paths all exited zero.
- Fixture composer decision identity
  `72eb3f4039cba26ffc449067cf038e4561a26fefe4c4b1f08e4cad29f033f0c6`
  withheld simulation training, physical transfer, and promotion.
- `py_compile` and `git diff --check` passed.

## Same-agent adversarial review

The complete sub-slice was reviewed for authority escalation, stale references,
unsafe defaults, non-finite values, evidence reuse/substitution, graph
ambiguity, ancestor/descendant double counting, path aliases, cleanup side
effects, input ordering, and documentation contradiction. Review-time
corrections added an actual physical-input branch to the same production schema,
bound evidence content to both device and calibration identity, and prevented
all custom production inputs from overwriting checked-in current-arm artifacts.

Reviewer decision 044 accepts the sub-slice locally. T16.4b remains
`in_progress`: remote preservation is pending, followed by the separate
numerical-hardening sub-slice.
