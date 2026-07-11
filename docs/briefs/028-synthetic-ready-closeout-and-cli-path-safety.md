# Slice Brief 028 - Synthetic Ready Closeout And CLI Path Safety

**Date:** 2026-07-10

## Objective

Close T16.4 by repairing custom absolute-path handling and implementing the
complete synthetic measured-inertial ready proof from brief 027. The real arm
must remain blocked and unqualified.

## Source Requirements

All acceptance criteria, negative tests, math rules, default-identity
preservation, and evidence requirements in
`docs/briefs/027-synthetic-measured-inertial-ready-closeout.md` remain required.
This brief adds the path-safety correction below.

## Path-Safety Correction

- Default tracked paths remain repo-relative in generated artifact references.
- A caller-provided absolute intake/output path outside the repo remains
  absolute; the CLI must not force it through `Path.relative_to(REPO_ROOT)`.
- Write and verify through external temporary absolute paths must work with
  correct file/semantic hashes.
- Invalid/tampered external input must fail before creating a new output and
  must leave an existing output byte-for-byte unchanged.
- Add direct CLI tests for external absolute write, verify, require-ready, and
  invalid-input no-overwrite behavior.

## Synthetic Ready Proof

- Add the clearly labeled `synthetic_test_only` fixture with multiple
  components, nonzero translations, and non-identity rotation.
- Implement exact measured coverage, CAD-inertia scaling, rotation, transformed
  component COM, aggregate COM, and parallel-axis summed inertia.
- Validate provenance, uncertainty, masses, frames/transforms, evidence reuse,
  exact cover, parent/child overlap, PSD/symmetry, principal-moment triangle
  inequalities, and finite values.
- Prove independently calculated golden mass/COM/full inertia, input-order
  invariance, and stable ready identity.
- The synthetic path must refuse either default real-artifact destination.

## Validation

- Run the full measured-inertial unit suite and syntax compilation.
- Run the real default write/verify path and intentional blocked
  `--require-ready` rejection.
- Run the bounded synthetic ready demo and record its output identity and golden
  aggregates.
- Run external absolute-path CLI regressions.
- Run the broader dependency-lock, twin-contract, structural-diff, and measured-
  inertial suite.

## Exit Condition

Fresh review confirms path safety plus every inherited brief-027 criterion. T16.4
may then close, while the current physical arm stays
`blocked_missing_measurements`. No hardware, qualification, or training work is
authorized in this slice.
