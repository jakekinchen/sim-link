# Reviewer Decision 290 - Verify T20.42 R0 Fixed Generation Result

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_42_R0_DATASET_ROUTE_T20_43_ACT`

## Findings

- Marker `1ff232aa...` was created before the first candidate and consumed the
  one-use permit `94d7f2b2...`. The completed result records one attempt and
  denies retry.
- The fixed manifest completed in exact order: 119/119 training candidates and
  9/9 fresh-held-out candidates pass unchanged strict-v2, with zero runtime or
  strict failures.
- Mixture `37b30d34...` includes the exact ten T20.23 base episodes once plus
  all 119 admitted R0 training episodes. The package contains 129 episodes and
  31,366 training frames.
- Fresh-held-out candidates and existing held-out seeds 6-7 contribute zero
  training or MEAN_STD rows. Statistics `02ba0e70...` are finite and strictly
  positive on every six-joint action/state channel.
- Result `d238379b...` binds the raw store, compiler, unpadded windows, package
  dataset, mixture, and statistics through retention receipt `19d19fba...`.
  The independent full verifier recomputes the boundary with exit 0.

## Adversarial review

- There is no duplicate base episode, held-out leakage, runtime-failure-as-
  success, missing candidate, output alias/symlink, non-finite statistic, or
  tree-identity discrepancy.
- The immutable pre-run marker correctly retains its before-first-candidate
  facts; terminal execution facts live in the separately signed result and are
  not back-written into the marker.
- All model, inference, optimizer, learned-rollout, Gate C, policy-acceptance,
  hardware, camera, serial, motion, network, external-compute, Brev, transfer,
  promotion, and R1-activation fields remain false. The R0 pass grants no such
  claim.
- A pre-marker shell timestamp-format error created no artifact and consumed no
  authority. The marker-bound run is the only attempt and no retry occurred.

## Verification

- Producer: exit 0, `verified_success`, result identity `d238379b...`.
- Independent `run_t20_42_r0_generation.py --verify`: exit 0 with identical
  counts and identity.
- Package readback: 129 episodes, 31,366 frames, zero held-out training rows,
  all prohibited authority flags false, and zero symlinked outputs.
- The earlier implementation gates remain green: 21 focused tests, 82 broad
  tests, eight MuJoCo source regressions, Ruff, compilation, and package smoke.

## Disposition

T20.42 and T20.42b are verified. Preserve the five compact generated artifacts
and this decision on origin, then open a fresh T20.43 brief for one bounded ACT
standard-recipe rung. T20.43 must pre-register its exact R0 Gate A parity,
official from-scratch ACT configuration, update/checkpoint schedule, selection
rule, both chunk-consumption variants, strict-v2 rollout evaluation, trace and
mirror retention, central authority, runtime preflight, and one-use permit
before optimizer creation.

## Authority withheld

No R1 activation from this decision alone; no model construction/load,
inference, optimizer creation/training, checkpoint, learned-policy rollout,
Gate C/D/E claim, retry, correction objective, threshold change, hardware,
camera, serial, physical motion, network/download, external compute, Brev,
physical transfer, promotion, or destructive operation.
