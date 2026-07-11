# Reviewer Decision 045 - Inertial Eigensolver Numerical Hardening Reviewed

**Date:** 2026-07-11

## Decision

`CLOSE T16.4b AFTER REMOTE PRESERVATION; CONTINUE T16.2b`

## Review target

Implementation commit `7d0562916c836810fc15c68ac51af20089a26dd7`
under Brief 036.

## Findings

- The symmetric 3x3 Jacobi solver normalizes by a finite matrix scale, uses a
  deterministic pivot order and fixed iteration bound, and fails closed on
  non-convergence or a non-finite iterate.
- Eigenvectors are retained and independently checked for `A*v=lambda*v`
  residuals and orthogonality before eigenvalues can drive PSD or rigid-body
  triangle decisions.
- Symmetry, PSD, and principal-moment triangle comparisons are scale-relative
  with a finite machine-precision floor. Signed zero and near-singular PSD
  tensors remain stable.
- Tolerated input asymmetry is first bounded, then averaged without overflow
  before the symmetric solve. Materially asymmetric tensors still fail closed.
- Randomized NumPy parity covers tiny, unit, and large scales, rotations,
  repeated/close eigenvalues, indefinite spectra, and near-singular spectra.
- The production fixture and checked-in blocked current-arm artifacts retain
  their exact identities. Neither component output grants global authority.

## Evidence

- 17 focused numerical/artifact-contract tests passed.
- 131 feeding/consuming tests passed in 69.913 seconds.
- An additional deterministic stress pass covered 20,000 eigensystems across
  exponents -300 through 300 and 2,000 randomized physical tensors; worst
  observed relative eigenvalue error was `1.821290090400898e-15`.
- Fixture input/output identities remained
  `fe9dbd5468a606019db735dc8664c05d5fc207d94bdcbc84243f58cfa98f869f`
  and `b8d7c5d287051aa863c3ef08597deefb9dd7685ad2c89d820456f92491fef25d`.
- Current-arm identity remained
  `8b8aab8e769167531776e38d76c545cec99277b69783d57c9db78f1020297ffc`
  with status `blocked_missing_measurements`.
- Default and fixture composer identities remained `d1206c5c...` and
  `72eb3f40...`; both withheld every global decision.
- Integrated production, dependency-lock, twin, structural-twin, and LeRobot
  product verifiers exited zero. `py_compile` and `git diff --check` passed.

## Review-time correction

The first implementation solved an accepted near-symmetric input directly,
which could make its stricter residual check reject noise already inside the
declared symmetry tolerance. The final implementation validates that bound and
solves the overflow-safe averaged symmetric part. Focused and broad gates were
rerun after the correction.

## Authority

After remote preservation, this closes T16.4b and establishes only
`production_inertial_compiler_valid` on the declared fixture-backed code path.
It does not establish current-arm physical inertials, physical qualification,
simulation-training readiness, physical transfer, deployment, promotion, or
optimizer authority. Hardware was not accessed and `training_lock` remains
closed.
