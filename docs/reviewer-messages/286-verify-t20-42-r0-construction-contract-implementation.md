# Reviewer Decision 286 - Verify T20.42/R0 Construction Contract Implementation

**Date:** 2026-07-16

## Decision

`ACCEPT_R0_CONTRACT_IMPLEMENTATION_REQUIRE_SEPARATE_GENERATION_AUTHORITY`

Brief 216 implementation `23cb5fb7a9d5739db869cce7f457be05791ad032`
is exact on `origin/codex/pi05-autolearn-loop`.

## Findings

- Construction specification `b58a6b31...` binds the owner decision at
  `e9d0507`, exact tracked T17.5b/T20.18/T20.23 sources, the verified ten-
  episode base, and existing held-out seeds 6-7.
- The deterministic five-by-five-by-five pose grid removes six historical
  overlaps and freezes 119 unique training candidates. All stay within the
  verified +/-1 mm / +/-0.03 rad envelope. Nine fresh held-out specifications
  use a disjoint +0.75 mm x band.
- Every initialization delta is zero because no nonzero initialization
  envelope is verified. Physics-parameter randomization, adaptive resampling,
  post-outcome mutation, implicit weighting, and optional new recovery branches
  are all disabled.
- Admission fixture `b7b1eb77...` includes the T20.23 ten-episode base exactly
  once plus 64 deterministic nominal-success witnesses. Its 74 training IDs
  are exactly the MEAN_STD statistics inputs; failed and held-out identities
  are disjoint and excluded.
- Preflight `5ff8c5cc...` binds the exact artifact files and product entrypoint,
  while `generation_ready=false` and every generation/model/optimizer/rollout/
  hardware/network/external-compute/Brev field remains false.
- The writer refuses overwrite and the verifier rejects source drift, signed
  semantic tampering, duplicate IDs/seeds/poses, out-of-envelope or non-finite
  values, held-out/statistics leakage, base omission/double counting, physics
  variation, authority escalation, path escape, and path aliases.

## Verification

- Eight focused T20.42 tests pass under minimal Python.
- Fifty-four broad artifact/compiler/pointer/T20.17/T20.18/T20.23/T20.42 tests
  pass in the cached offline Python 3.12 runtime.
- Eight scripted-expert/T20.23 source regressions pass with cached MuJoCo
  3.3.5.
- Exact CLI verification, Ruff, Python compilation, JSON, artifact hashes,
  count/uniqueness/disjointness audit, pointer check, and diff check pass.

## Disposition

Accept the implementation boundary and continue T20.42 under Brief 216 only
to a fresh generation-authority design/review slice. Do not execute the fixed
candidate manifest until an exact implementation commit, central decision,
runtime preflight, one-use permit, and separate pre-run reviewer decision all
agree on origin.

## Authority withheld

No R0 episode generation, dataset materialization, model construction/load/
inference, optimizer creation/training, learned-policy rollout, Gate C/D/E
claim, threshold change, archive replay, hardware/camera/serial access,
physical motion, network/download, external compute, Brev, physical transfer,
promotion, destructive operation, or R1 activation.
