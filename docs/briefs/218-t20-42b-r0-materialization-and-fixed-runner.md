# Slice Brief 218 - T20.42b R0 Materialization And Fixed Runner

**Date:** 2026-07-16

## Objective

Implement and fixture-test the live runtime collector, exact authority-
artifact materializer, and sole fixed-manifest R0 runner needed to execute the
reviewed T20.42/T20.42a contracts. Preserve and review the implementation on
origin before materializing authority; then preserve and separately review the
pre-run artifacts before creating the one-use marker or executing MuJoCo.

## Owner window and source boundary

- The owner's fresh simulation-only authorization is active from
  `2026-07-16T12:35:56-05:00` through `2026-07-16T20:35:56-05:00` for exactly
  one fixed 119-training-candidate plus nine fresh-held-out-candidate R0
  attempt. No new major slice begins after `19:50:56` CDT.
- Bind Reviewer 287 review commit
  `e8127e22519ba8354d1999f8b24353b600722e39`, T20.42a implementation
  `c2a4512346e7d92bc26a4d25375b9738cb5e5cda` plus hardening
  `953067175ed286a98404651e3b2c6e548e22e5f0`, and the exact T20.42 compact
  source/file hashes already frozen by Briefs 216-217.
- The future owner grant and runtime preflight must bind the full reviewed
  implementation commit produced by this brief and confirmed on origin.

## Implementation boundary before materialization

- Add a live collector that reads only local branch/HEAD/origin ancestry,
  scoped dirt, dependency/platform versions, free disk, and fixed output-path
  lstat state. It must never repair, download, import a fallback checkout, or
  create an output while collecting facts.
- Add an exclusive, no-overwrite authority materializer for the owner grant,
  central request/decision, runtime preflight, and one-use permit. Build all
  five in memory, verify them independently, then write exact canonical bytes
  only after every target is absent and unaliased. Partial authority writes
  fail closed and do not authorize a marker.
- Add the fixed R0 runner by reusing the verified scripted expert, strict-v2
  evaluator, append-only raw-store, frame/segment compiler, unpadded-window,
  and package LeRobotDataset paths. Do not create a model or optimizer.
- The implementation and fixture tests must be committed, pushed, and accepted
  by a fresh same-agent reviewer before live authority materialization.

## Pre-run materialization and review boundary

- Materialize the exact five compact authority artifacts only while the owner
  window is active and the reviewed implementation commit is HEAD and present
  on origin. The scoped implementation tree must be clean; unrelated preserved
  dirt remains outside the scoped list.
- Bind exact offline dependency versions, platform, at least 10 GiB free disk,
  network/fallback disabled, and every one of the ten fixed output paths absent
  and unaliased.
- Commit and push only the compact authority artifacts and state/review docs.
  A fresh pre-run reviewer must reconstruct every artifact, confirm origin,
  re-check the active window and output absence, and explicitly accept the sole
  marker/run before execution.

Implementation commits `d24ad0e78db59a4facb7de664a8e1a42dbcabc2e`
and `c435809896ae0155405682bff3ec655d8264db74` are exact on origin. Reviewer
288 accepts the collector/materializer/fixed-runner implementation and opens
only the five-artifact compact materialization step. The live collector reports
zero scoped dirt, all ten outputs absent/unaliased, exact offline dependencies,
and more than 73 GB free. The pre-run acceptance, marker, and R0 execution
remain closed until the materialized boundary is separately preserved and
accepted by Reviewer 289.

Authority commit `93d7708222d6f564a37f25289957fe55736725b2` is now exact
on origin. Reviewer 289 independently reconstructs owner grant `b5d08b77...`,
request `5c5b99fc...`, decision `f6121762...`, runtime `ffa95218...`, and
one-use permit `94d7f2b2...`; the active window, unchanged implementation,
offline dependency facts, free disk, and output absence all pass. Signed
pre-run acceptance `97694eb5...` binds that review and authority commit. Once
this acceptance boundary is confirmed on origin, the one fixed marker/run is
eligible; every excluded action remains closed.

## Sole attempt and result rules

- After pre-run acceptance, create the immutable marker first. That consumes
  the permit even if dependency initialization or the first candidate fails.
- Execute each of the 119 training candidates and nine fresh-held-out
  candidates exactly once and in permit order. No retry, replacement,
  resampling, candidate mutation, physics randomization, or seed-6/7
  regeneration is allowed.
- Retain every strict-v2 outcome. Only new training-candidate strict successes
  may enter training. Failures/quarantines and all fresh-held-out evidence stay
  outside training and MEAN_STD statistics.
- If fewer than 64 new training candidates pass strict-v2, retain the raw
  evidence and write a signed terminal negative without materializing the R0
  LeRobotDataset. No retry is authorized.
- On 64-119 successes, compile the append-only raw store through exact hard-
  boundary frames/segments and unpadded windows, include the exact T20.23 base
  once, materialize one package LeRobotDataset, compute MEAN_STD from frozen
  training rows only, and write compact signed result, mixture, statistics, and
  retention evidence.

## Verification

- Tests first cover dirty/branch/origin/dependency/disk/output drift, path
  escape/alias/collision, partial materialization, stale owner time, artifact
  reconstruction, marker ordering, duplicate/unknown/out-of-order candidates,
  strict-v2 admission, held-out/statistics leakage, base omission/double count,
  insufficient-success negative routing, and every prohibited authority field.
- Run focused tests, relevant broad compiler/dataset/source regressions, Ruff,
  compilation, strict JSON, pointer, identity/count/order, output-absence, diff,
  and two fresh same-agent adversarial reviews at the implementation and pre-run
  boundaries.

## Authority withheld

No authority-artifact materialization before the implementation review; no
attempt marker or MuJoCo candidate before the separate pre-run review; no
second attempt, retry, adaptive manifest extension, model construction/load/
inference, optimizer creation/training, learned-policy rollout, Gate C/D/E
claim, threshold change, archive replay, hardware/camera/serial access,
physical motion, network/download, external compute, Brev, physical transfer,
promotion, destructive operation, or R1 activation.
