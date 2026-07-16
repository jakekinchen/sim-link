# Reviewer Decision 289 - Accept T20.42b R0 Pre-Run Authority

**Date:** 2026-07-16

## Decision

`ACCEPT_ONE_FIXED_T20_42_R0_ATTEMPT`

Authority commit `93d7708222d6f564a37f25289957fe55736725b2` is
exact on `origin/codex/pi05-autolearn-loop`. The reviewed implementation commit
is `c435809896ae0155405682bff3ec655d8264db74`.

## Reconstructed authority

- Owner grant: `b5d08b776739a0f9098b3c5f05c95b8e6a4e14a7ae5e71b9733fc8440d401cb2`.
- Central request: `5c5b99fccb0e8bf4422ec6396c6c106662ad23fec3c8cd94c1838611299eaf94`.
- Central decision: `f612176216e9555070124d36a848e57e80631c66a68e481bd3ed525a9cf734ba`;
  it grants only `simulation_training_ready`.
- Runtime preflight: `ffa952189e862258a3097aa60194334be786155ea086073726e7fdbcf57cd828`.
- One-use permit: `94d7f2b21045e80c84d54678bdd8e1e5a92dac85dce96ce38bc211df12de55ea`.

All five reconstruct exactly from the reviewed T20.42 sources. Their tracked
file hashes are respectively `d8af6cab...`, `7568a3a9...`, `0a98a226...`,
`64b7cf9d...`, and `dbeeb59b...` in owner/request/decision/preflight/permit
order.

## Pre-run findings

- The owner window is active from `2026-07-16T12:35:56-05:00` through
  `20:35:56-05:00`; the audit occurred at 13:07 CDT.
- `93d7708` is on the origin tracking ref. The complete implementation-scoped
  file set has zero diff from `c435809` and zero dirty paths.
- Runtime facts are Python 3.12.12, MuJoCo 3.3.5, NumPy 2.2.6, Pillow 12.3.0,
  PyArrow 25.0.0, and package LeRobot 0.6.1. Network and dependency fallback
  are disabled.
- Free disk is approximately 73.3 GB, above the frozen 10-GiB floor.
- The pre-run acceptance, attempt marker, run root, result, mixture,
  statistics, and retention paths are absent and unaliased. Every permit output
  was absent at runtime-preflight capture.
- The permit contains exactly 119 ordered training candidates and nine ordered
  fresh-held-out candidates, references existing seeds 6-7 without regeneration,
  permits one attempt, and forbids retry or manifest extension.

## Adversarial disposition

Source/hash/order/split/commit drift, held-out leakage, output collision or
alias, stale authority, implementation changes, and an unpreserved reviewer
acceptance all fail before the marker. Once the signed acceptance is preserved
on origin, the runner may create exactly one marker and execute exactly the
fixed manifest. Fewer than 64 new training strict successes must terminate
negative without dataset materialization; 64-119 may proceed through the exact
base-once/package-dataset/MEAN_STD evidence route.

## Authority granted

- Write and preserve the signed Reviewer 289 pre-run acceptance bound to this
  document and authority commit.
- After that acceptance commit is confirmed on origin and the owner window is
  still active, create the one immutable permit-consuming marker and execute
  the fixed 119+9 simulation-only R0 attempt once.
- Retain all strict/runtime outcomes and write only the pre-registered
  success or terminal-negative evidence bundle.

## Authority withheld

No second attempt, retry, replacement/resampling, adaptive manifest extension,
seed-6/7 regeneration, physics randomization, model construction/load/inference,
optimizer creation/training, learned-policy rollout, Gate C/D/E claim,
threshold change, archive replay, hardware/camera/serial access, physical
motion, network/download, external compute, Brev, physical transfer, promotion,
destructive operation, or R1 activation.
