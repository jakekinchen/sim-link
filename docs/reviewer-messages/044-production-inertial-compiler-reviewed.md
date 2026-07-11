# Reviewer Decision 044 - Production Inertial Compiler Reviewed

**Date:** 2026-07-11

## Decision

`CONTINUE T16.4b NUMERICAL HARDENING AFTER REMOTE PRESERVATION`

## Review target

Implementation commit `a93ff057f8cf4f966d4edc8dc0098c3526a14def`
under Brief 035.

## Findings

- The production v2 intake is a rooted acyclic hierarchy with one parent and
  transform edge per non-root component, unique frames, derived required-leaf
  coverage, and explicit ancestor/descendant rejection.
- The six required source modes share one strict production compiler. Scale
  evidence derives mass only; every COM and inertia derivation is separate and
  mode-specific.
- Raw/native and SI values, units, metrology, assumptions, approximation
  uncertainty, evidence hashes, device identity, and calibration identity are
  preserved and verified.
- Internal transform and aggregation math is unrounded and finite-checked;
  serialization is the only rounding boundary.
- Fixture evidence is explicitly non-physical, cannot overwrite current-arm
  artifacts, and cannot grant a global composer decision. The checked-in current
  arm remains blocked.
- The same schema can compile content-addressed physical inputs into local
  inertial capability facts only. Global decisions remain central-composer
  outputs.

## Evidence

- 21 focused tests passed in 23.172 seconds.
- 122-test broad gate passed in 71.332 seconds.
- Fixture and integrated product verifiers exited zero.
- Fixture input/output identities: `fe9dbd5468a606019db735dc8664c05d5fc207d94bdcbc84243f58cfa98f869f`
  and `b8d7c5d287051aa863c3ef08597deefb9dd7685ad2c89d820456f92491fef25d`.
- Fixture authority composition identity
  `72eb3f4039cba26ffc449067cf038e4561a26fefe4c4b1f08e4cad29f033f0c6`
  withheld every global decision.
- Static imports and `git diff --check` passed.

## Authority

After remote preservation, this sub-slice may establish only
`production_inertial_compiler_fixture_valid`. It grants no current-arm physical
measurement evidence, simulation-training readiness, physical qualification,
physical transfer, deployment, promotion, or optimizer authority.

## Remaining T16.4b gate

Add deterministic eigensolver convergence and residual validation,
scale-relative tolerances, randomized NumPy comparisons, rotation invariance,
tiny/large-scale and near-singular/slightly-indefinite coverage, and non-finite
rejection. Do not close T16.4b before that sub-slice is reviewed and remotely
preserved.
