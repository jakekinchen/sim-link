# Session 048 - Inertial Eigensolver Numerical Hardening

**Date:** 2026-07-11

## Scope

Execute Brief 036 as the final numerical sub-slice of T16.4b. No hardware,
optimizer, paid compute, physical evidence, or authority expansion was used.

## Implementation

- Replaced the absolute-threshold eigenvalue-only path with a deterministic,
  scale-normalized symmetric 3x3 Jacobi eigendecomposition.
- Added a fixed iteration limit, explicit convergence failure, finite-iterate
  checks, eigenvector retention, normalized eigenpair residual checks, and
  orthogonality checks.
- Made symmetry, positive-semidefinite, and rigid-body triangle comparisons
  scale-relative with a machine-precision floor.
- Bounded tolerated asymmetric roundoff and solved its overflow-safe averaged
  symmetric part.
- Added deterministic NumPy parity and adversarial tests across rotations,
  tiny/large scales, near-singular and slightly indefinite tensors, repeated
  eigenvalues, signed zero, non-finite inputs/results, iteration exhaustion,
  and injected residual failure.

## Evidence

- Implementation commit: `7d0562916c836810fc15c68ac51af20089a26dd7`.
- Focused numerical/artifact suite: 17 tests passed.
- Broad feeding/consuming gate: 131 tests passed in 69.913 seconds.
- Additional stress: 20,000 random eigensystems across exponents -300 through
  300 and 2,000 randomized physical tensors; worst relative NumPy error
  `1.821290090400898e-15`.
- Fixture, integrated measured-inertial, blocked current-arm, default composer,
  fixture composer, dependency lock, twin, structural twin, and LeRobot product
  paths all exited zero.
- Fixture identities remained `fe9dbd54...` -> `b8d7c5d2...`; current-arm
  identity remained `8b8aab8...` and blocked; composer decisions remained
  `d1206c5...` and `72eb3f40...` with no authority granted.
- `py_compile` and `git diff --check` passed.

## Same-agent adversarial review

The complete diff was freshly reviewed for premature convergence, hidden
absolute tolerances, scale overflow/underflow, eigenvector drift, residual
normalization, nondeterministic pivot ties, signed zero, repeated spectra,
rotation sensitivity, tolerated asymmetry, real negative-eigenvalue acceptance,
non-finite intermediates, and downstream authority escalation. Review-time
correction symmetrized only after the declared asymmetry bound was validated.
All final gates were rerun.

Reviewer decision 045 accepts the implementation locally. T16.4b remains
`in_progress` until implementation and reviewer evidence are pushed and
independently confirmed on `origin/codex/pi05-autolearn-loop`.

## Remote closeout

Pending scoped reviewer-evidence commit, push, and independent remote
confirmation.
