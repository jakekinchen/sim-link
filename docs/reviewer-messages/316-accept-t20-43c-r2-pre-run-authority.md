# Reviewer Decision 316 - Accept T20.43c-R2 Pre-Run Authority

**Date:** 2026-07-16

## Decision

`ACCEPT_ONE_T20_43C_MANUAL_REPLACEMENT`

Authority commit `391811e098b65d8d22e4a6d646fc3293ab3f9b63` is exact on
`origin/codex/pi05-autolearn-loop` and descends from reviewed implementation
boundary `1bc1c7731debd657a5cf97b892b67fc74ec3d2a4`.

## Reconstructed authority

- Actual-schema smoke `9e8783dc...`, file SHA `1c53c4ee...`; it dispatches the
  exact `scenesmith.t20_43b_r1_act_rollout.v1` schema emitted by every R2
  evaluation and binds MP4 `955ad918...` plus manifest `00494310...`.
- Owner authorization `d95ddd8a...`, file SHA `e4b8471f...`.
- Central request `1f528d2e...`, file SHA `8be2803a...`.
- Central decision `bf7908b5...`, file SHA `3240a316...`; it grants exactly
  `simulation_training_ready`.
- Runtime preflight `79689c7f...`, file SHA `d4901ab5...`.
- One-use permit `f063e034...`, file SHA `140d1b3f...`.

All six artifacts reconstruct through the reviewed live verifier. The owner
interval is `2026-07-16T23:07:00-05:00` through
`2026-07-17T07:00:00-05:00`.

## Pre-run findings

- Prior terminal interruption `d848a1a8...`, equivalence `85087b2a...`, first
  continuation marker `e086c293...`, and partial tree `e0aea95f...` remain
  immutable. Exact update-728 resume remains impossible because optimizer state
  was not retained.
- Required source `1bc1c773...` and authority commit `391811e...` are exact on
  origin. R2 implementation and authority paths are clean despite unrelated
  preserved reconstruction-kit worktree dirt.
- The existing signed actual-schema smoke is re-executably verified against the
  exact renderer and source trace. R2 produces no other rollout-trace schema.
- Python 3.12.12, torch 2.11.0, torchvision 0.26.0, datasets 4.8.5, MuJoCo
  3.3.5, NumPy 2.2.6, Pillow 12.3.0, PyArrow 25.0.0, and LeRobot 0.6.1 are
  pinned; MPS is available and network use is false.
- Live review observed more than 27,800 seconds remaining against the required
  14,400-second completion budget and approximately 28.6 GB free.
- Acceptance, marker, run root, equivalence, result, terminal failure, and final
  receipt paths were absent and unaliased. No checkpoint tensor read, model
  construction/load/inference, optimizer, rollout, or Gate C action occurred.
- Nineteen focused authority, pointer, and R2 tests pass.

## Adversarial disposition

Stale origin, dirty or untracked implementation inputs, renderer/schema drift,
output collision or aliasing, non-finite evidence, authority escalation,
automatic retry, recipe/schedule/data/threshold mutation, and
hardware/network/external/Brev authority all fail closed. The marker consumes
the sole replacement before checkpoint tensor or model action. Update 1 remains
barred until fresh seeded ACT tensors are bit-exact to checkpoint 0, AdamW has
zero state entries, and the sampler has consumed zero batches.

## Authority granted

- Write one signed acceptance bound to this decision, permit, and authority
  commit.
- After this decision and acceptance are exact on origin and the completion
  budget still exceeds four hours, create the sole R2 replacement marker.
- Prove zero-update equivalence, then execute the unchanged ACT updates
  1-10,000 and fixed seven-checkpoint dual-semantics evaluations once.
- Preserve either the first strict-v2 Gate C pass or the exact terminal
  negative/failure with complete local evidence and compact signed receipts.

## Authority withheld

No retry after the replacement marker, second replacement, exact-resume claim,
sweep, recipe/schedule/data/threshold change, correction objective, T20.45
activation, hardware, camera, serial, physical motion, network, package
installation, external compute, Brev, transfer, promotion, or destructive
operation.
