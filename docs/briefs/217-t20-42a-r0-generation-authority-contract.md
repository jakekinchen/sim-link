# Slice Brief 217 - T20.42a R0 Generation Authority Contract

**Date:** 2026-07-16

## Objective

Implement and fixture-test the exact central request, runtime preflight,
one-use permit, and attempt-marker contracts required to execute the fixed R0
manifest from Brief 216. This slice may materialize no authority artifact and
may execute no candidate. Its output is reviewable code for a later separately
authorized pre-run boundary.

## Exact source boundary

- Bind construction implementation
  `23cb5fb7a9d5739db869cce7f457be05791ad032` and Reviewer 286 boundary
  `c87ee846cd475b4a46bb66ed1ba1aae6642040af` on origin.
- Bind construction spec `b58a6b31...` / file `accb216d...`, admission fixture
  `b7b1eb77...` / file `ee5ff97f...`, and construction preflight
  `5ff8c5cc...` / file `e7558a46...` without rewriting them.
- Bind the owner T20.41 route decision, the exact T17.5b/T20.18/T20.23 source
  identities carried by the spec, and the central composer implementation.
- The permit must contain exactly 119 training-candidate IDs, nine fresh-
  held-out IDs, and existing held-out seeds `[6, 7]` as references only.

## Authority contract

- Recompose a central `simulation_training_ready` request/decision for this
  simulation-only data-generation purpose. The global decision may grant only
  `simulation_training_ready`; action scope is narrowed separately by the
  owner grant and one-use permit.
- Authorized permit actions are exactly: execute the fixed scripted-expert
  manifest once, retain strict-v2 outcomes and quarantines, compile the
  append-only raw store through the existing frame/segment/window path,
  materialize one package LeRobotDataset with the exact T20.23 base once plus
  admitted new successes, compute MEAN_STD from frozen training rows only, and
  write compact signed result/mixture/statistics evidence.
- Strict-v2 failures are expected evidence and do not widen or retry the
  manifest. Source/hash/commit drift, non-finite values, path aliasing, output
  collision, permit mismatch, or authority escalation fail before generation.
- Write an immutable attempt marker before the first MuJoCo candidate. The
  marker consumes the permit even if startup or generation later fails. No
  second marker or retry is allowed.

## Runtime preflight contract

- Require exact branch, clean scoped implementation tree, origin ancestry, and
  the reviewed source commit selected by the future materializer.
- Reverify all three T20.42 compact artifacts, candidate counts/IDs, source
  references, route decision, and authority request/decision without executing
  a candidate.
- Bind Python, MuJoCo, NumPy, Pillow, PyArrow, package LeRobot, and platform
  metadata needed by the later runner. Network and fallback stay disabled.
- Require all final output roots, attempt marker, result, dataset, raw store,
  compiler/window outputs, and compact receipt paths absent. Reject symlinks or
  paths outside the checkout.
- Require at least 10 GiB free disk. The existing eight-episode raw store is
  approximately 95 MiB and the ten-episode LeRobotDataset approximately 63
  MiB; the threshold leaves ample headroom for the fixed 128 new evaluations.

## Verification

- Tests first cover exact source and candidate binding, central decision scope,
  permit action/count/order drift, duplicate/unknown candidate IDs, seed-6/7
  regeneration, wrong commit/branch/origin state, dirty scoped paths, missing
  dependencies, network/fallback enablement, insufficient disk, present or
  aliased outputs, marker-first consumption, duplicate markers, non-finite
  runtime facts, signed tampering, and every prohibited authority field.
- The prospective contracts must reconstruct byte-for-byte from fixture
  runtime facts while leaving every output and attempt path absent.
- Focused and relevant broad tests, Ruff, compilation, JSON, pointer, diff, and
  same-agent adversarial review must pass before implementation is accepted.

## Authority withheld

No authority artifact materialization, attempt marker, R0 episode generation,
dataset materialization, model construction/load/inference, optimizer creation/
training, learned-policy rollout, Gate C/D/E claim, threshold change, archive
replay, hardware/camera/serial access, physical motion, network/download,
external compute, Brev, physical transfer, promotion, destructive operation,
or R1 activation. A later pre-run reviewer decision must bind exact authority
artifacts to an origin-confirmed implementation before any marker may exist.
