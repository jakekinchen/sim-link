# Reviewer Decision 288 - Verify T20.42b R0 Materializer/Runner Implementation

**Date:** 2026-07-16

## Decision

`ACCEPT_R0_MATERIALIZER_RUNNER_IMPLEMENTATION_AUTHORIZE_COMPACT_PRE_RUN_MATERIALIZATION_ONLY`

Implementation commits `d24ad0e78db59a4facb7de664a8e1a42dbcabc2e`
and `c435809896ae0155405682bff3ec655d8264db74` are exact on
`origin/codex/pi05-autolearn-loop`.

## Findings

- The live collector is read-only and binds the reviewed implementation as an
  unchanged ancestor of an origin-confirmed HEAD. It checks exact branch,
  scoped dirt/diff, local dependency/platform versions, free disk, authority
  absence, and all ten fixed output-path lstat states without network or
  fallback behavior.
- The materializer builds all five reviewed T20.42a payloads in memory, verifies
  them independently, rejects any existing/aliased target before the first
  write, and uses exclusive canonical writes. Partial writes cannot create a
  valid reviewed run boundary.
- The runner independently compares permit order with the construction plan,
  validates all 128 zero-initialization/no-physics candidates, requires the
  signed Reviewer 289 pre-run acceptance preserved at HEAD, and creates the
  immutable permit-consuming marker before the raw-store root or first MuJoCo
  call.
- Every completed/runtime-failed and strict-pass/fail outcome remains in fixed
  order. Only training-split strict successes are admitted; fresh-held-out
  candidates and seeds 6-7 contribute zero training/statistics rows.
- The fewer-than-64 route writes a signed terminal negative without a dataset.
  The success route copies the exact verified T20.23 base once, appends admitted
  successes, finalizes one package LeRobotDataset, derives training-only
  MEAN_STD, and binds compiler/window/dataset trees through compact signed
  mixture/result/retention evidence.

## Adversarial review

- Canonical JSON sort-on-write no longer causes false output-map order drift;
  the verifier still requires the exact fixed path set and exact state values.
- Source substitution, candidate duplication/unknown/order drift, split
  relabelling, runtime-failure-as-pass, held-out leakage, non-finite/nonpositive
  statistics, base duplication, path escape/alias/collision, stale owner time,
  implementation drift after review, and unpreserved pre-run acceptance all
  fail closed.
- The bounded source-expert entrypoint validates only the previously proven
  pose envelope and grants no manifest/training/retry authority; the original
  T17.5b fixed-seed path remains its default exact behavior.
- No cleanup deletes a marker or raw evidence, no failed route opens a retry,
  and no model, optimizer, hardware, camera, serial, network, external-compute,
  Brev, transfer, promotion, Gate C, or R1 authority enters any result surface.

## Verification

- 21 focused T20.42a/b tests pass.
- 82 relevant broad authority/compiler/window/T20 tests pass.
- Eight scripted-grasp/T20.23 source regressions pass with MuJoCo 3.3.5.
- A local offline package smoke copied verified base frames into a temporary
  LeRobotDataset and recovered finite action/state statistics.
- The live collector at `c435809...` reports Python 3.12.12, MuJoCo 3.3.5,
  NumPy 2.2.6, Pillow 12.3.0, PyArrow 25.0.0, LeRobot 0.6.1, zero scoped dirt,
  all ten outputs absent/unaliased, and 73.3 GB free.
- Ruff, compilation, strict JSON, remote-head, output-absence, and diff checks
  pass.

## Disposition

The implementation review boundary is accepted. While the owner window is
active, materialize only the five compact authority artifacts bound to
`c435809...`, commit and push them, and perform Reviewer 289's separate pre-run
reconstruction. Do not create the acceptance artifact, marker, raw store, or
first R0 candidate until that second review explicitly accepts the one attempt.

## Authority withheld

No pre-run acceptance, attempt marker, R0 episode generation, dataset
materialization, model construction/load/inference, optimizer creation/training,
learned-policy rollout, Gate C/D/E claim, threshold change, archive replay,
hardware/camera/serial access, physical motion, network/download, external
compute, Brev, physical transfer, promotion, destructive operation, retry, or
R1 activation.
