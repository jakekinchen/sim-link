# Slice Brief 036 - Inertial Eigensolver Numerical Hardening

**Date:** 2026-07-11

## Objective

Complete the final T16.4b numerical gate. Harden the deterministic symmetric
3x3 eigensolver used by the artifact contract so inertia validity is reliable
across scale, near-singular tensors, rotations, and adversarial finite inputs.

## Acceptance criteria

- Use scale-relative symmetry, PSD, rigid-body triangle, convergence, and
  residual tolerances. Do not use a fixed absolute tolerance that changes
  semantics across tiny and large tensors.
- Return or internally retain deterministic eigenvectors as needed to verify
  `A*v=lambda*v` residuals.
- Fail closed if Jacobi iteration does not converge within a fixed deterministic
  bound or if a normalized residual exceeds its declared tolerance.
- Reject every non-finite input and any non-finite intermediate or eigen result.
- Preserve correct acceptance for zero and near-singular PSD tensors while
  rejecting slightly indefinite tensors at comparable relative scale.
- Preserve inertia validity under proper rotation.
- Compare a deterministic randomized corpus against `numpy.linalg.eigvalsh`
  across tiny, unit, and large scales, including repeated/close eigenvalues and
  rotated tensors.
- Keep the production measured-inertial fixture, blocked current-arm artifact,
  authority composer, twin, structural-twin, and LeRobot-stack gates green.

## Adversarial review focus

- convergence hidden by premature thresholding;
- scale overflow/underflow;
- eigenvector drift and residual normalization;
- signed zero and repeated eigenvalues;
- symmetry tolerance accidentally accepting a materially asymmetric tensor;
- tolerance large enough to accept a real negative eigenvalue;
- rotation-induced false rejection; and
- nondeterministic pivot selection.

## Validation

- Focused artifact-contract numerical suite, including randomized NumPy parity.
- Production and legacy measured-inertial suites.
- Authority, twin, structural-twin, LeRobot stack, and dependency-lock broad
  gate.
- Fixture and blocked-current-arm product verifiers.
- `py_compile` and `git diff --check`.

## Out of scope

Qualification metric computation, hardware access, optimizer work, physical
transfer, deployment, and promotion.

## Authority after this slice

If reviewed and remotely preserved, this closes T16.4b and may establish only
`production_inertial_compiler_valid` on the declared fixture evidence. It does
not establish current-arm physical inertials or any global authority.
