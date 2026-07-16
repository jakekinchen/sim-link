# Reviewer Decision 287 - Verify T20.42a R0 Generation Authority Contract

**Date:** 2026-07-16

## Decision

`ACCEPT_R0_GENERATION_AUTHORITY_CONTRACT_IMPLEMENTATION_REQUIRE_SEPARATE_MATERIALIZATION_AND_PRE_RUN_REVIEW`

Implementation commits `c2a4512346e7d92bc26a4d25375b9738cb5e5cda`
and `953067175ed286a98404651e3b2c6e548e22e5f0` are exact on
`origin/codex/pi05-autolearn-loop`.

## Findings

- The module re-verifies the exact T20.42 construction specification
  `b58a6b31...`, admission fixture `b7b1eb77...`, construction preflight
  `5ff8c5cc...`, their tracked file hashes, and the inherited T20.23 central
  simulation-training decision before composing any prospective authority.
- The central composer mechanically grants only `simulation_training_ready`.
  The owner grant and permit narrow that global state to six exact R0 data-
  generation actions, one attempt, 119 ordered training candidates, nine
  ordered fresh-held-out candidates, and seeds 6-7 as reference-only evidence.
- Runtime preflight fails on source/branch/origin/scoped-dirty drift, missing
  dependency or platform metadata, network/fallback enablement, less than 10
  GiB free disk, output collision, symlink aliasing, non-strict runtime facts,
  or any authority/reference mismatch.
- The permit freezes all ten attempt/output paths and cannot regenerate seeds,
  widen the manifest, retry, or grant model/optimizer, hardware, network,
  external-compute, Brev, transfer, promotion, or R1 authority.
- The attempt marker is signed, source-commit and time-window bound, created
  before the first candidate, and written with exclusive no-follow semantics.
  Once file creation succeeds it is never removed, so partial startup failure
  still consumes the sole permit.

## Adversarial review

- Authority escalation is rejected both by exact reconstruction and explicit
  false fields. The composer graph is unchanged and admits no component-
  supplied global authority field.
- Stale or substituted source identities, file hashes, candidate IDs/order,
  held-out membership, and prospective artifact references fail closed.
- Candidate IDs are unique and disjoint across training/fresh-held-out sets;
  the exact T20.23 base remains once-only and training-only MEAN_STD is frozen.
- Runtime paths are fixed repository-relative names. Output-state aliases and
  an actual symlinked marker parent are rejected; existing markers cannot be
  overwritten.
- No cleanup path deletes a consumed marker, no unordered set enters a signed
  payload, and reconstruction from the supplied fixture facts is byte-exact.
- The implementation imports no runner, model, optimizer, hardware, camera,
  serial, network, or external-compute surface and exposes no authority-
  artifact materializer or R0 generation entrypoint.

## Verification

- Nine focused T20.42a tests pass under minimal Python.
- Seventy relevant broad contract/compiler/T20 tests pass in the cached
  offline Python 3.12/MuJoCo runtime.
- Eight scripted-grasp/T20.23 source regressions pass with MuJoCo 3.3.5.
- Ruff, Python compilation, exact T20.42 CLI verification, strict JSON,
  project-state pointer, output-absence, remote-head, and diff checks pass.

## Disposition

Accept Brief 217's implementation contract only. A fresh brief must bind an
active owner window, materialize the exact prospective authority artifacts,
collect live runtime facts, preserve that pre-run boundary on origin, and pass
another reviewer decision before an attempt marker or MuJoCo candidate may
exist. T20.42/R0 remains in progress; T20.43/R1 remains closed.

## Authority withheld

No authority-artifact materialization, attempt marker, R0 episode generation,
dataset materialization, model construction/load/inference, optimizer creation/
training, learned-policy rollout, Gate C/D/E claim, threshold change, archive
replay, hardware/camera/serial access, physical motion, network/download,
external compute, Brev, physical transfer, promotion, destructive operation,
or R1 activation.
