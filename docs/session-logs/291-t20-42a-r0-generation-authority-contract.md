# Session Log 291 - T20.42a R0 Generation Authority Contract

## Implementation

- Added a pure-Python, construction-only authority module for the reviewed
  T20.42/R0 boundary. It builds and verifies a prospective owner grant,
  central composition request/decision, runtime preflight, one-use permit,
  and immutable attempt marker without materializing any of them.
- Bound the exact T20.42 construction specification `b58a6b31...`, admission
  fixture `b7b1eb77...`, construction preflight `5ff8c5cc...`, their tracked
  file hashes, and the inherited T20.23 central simulation-training decision.
- Froze the permit to the ordered 119 training candidates, nine fresh held-out
  candidates, and existing held-out seeds 6-7 as references only. The exact
  six allowed actions contain no model, optimizer, hardware, network,
  external-compute, Brev, transfer, promotion, or R1 authority.
- Added fail-closed runtime checks for the exact branch/source commit/origin
  state, clean scoped paths, required dependency and platform metadata,
  network/fallback disablement, at least 10 GiB free disk, and ten absent,
  unaliased output paths.
- Made marker creation exclusive and non-overwriting. Creation consumes the
  one-use permit before the first candidate; no failure after file creation
  removes or reopens that marker.

## Evidence

- Nine focused T20.42a tests pass under minimal Python, including exact source
  and central-decision scope, source-hash and authority-window drift, runtime
  failures, duplicate/unknown candidates, seed regeneration, re-signed
  tampering, marker ordering, and exclusive-write behavior.
- Seventy broad artifact, authority-composer, compiler, window, T20.17,
  T20.18, T20.23, T20.42, and T20.42a tests pass in the cached offline Python
  3.12/MuJoCo runtime.
- Eight scripted-grasp/T20.23 source regressions pass with cached MuJoCo 3.3.5.
- Ruff formatting/check, Python compilation, exact T20.42 CLI verification,
  strict JSON, project-state pointer, output-absence, and diff checks pass.

## Result

The authority-contract implementation is ready for exact origin review. This
is not a generation-authority artifact boundary: no owner grant, central
request/decision, runtime preflight, permit, attempt marker, R0 output, model,
optimizer, hardware, network, external compute, or Brev action exists. A
separate materialization/pre-run brief and reviewer decision remain required
before any marker or MuJoCo candidate may execute.
