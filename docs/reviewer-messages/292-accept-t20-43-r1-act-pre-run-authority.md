# Reviewer Decision 292 - Accept T20.43 R1 ACT Pre-Run Authority

**Date:** 2026-07-16

## Decision

`ACCEPT_ONE_T20_43_R1_ACT_STANDARD_ATTEMPT`

Authority commit `2f2a2caa195fdae0e49a3b3f6d56359876d083e8` is
exact on `origin/codex/pi05-autolearn-loop`. The reviewed implementation commit
is `9a03a86c05a00afbdb1d37878fd78e07a9b4c22b`.

## Reconstructed authority

- Gate A: `90217d2b2e91c95d4c3dd3b0538dc215bf5042b00b5e22313be4b09bb2e63b8a`.
- Owner grant: `60b3b8cb1c8b5975057d0e54ea16738500495cb466d09a1b384b0bd7b401295a`.
- Central request: `79e190dd3c2714867e2797067e8ac5f0ef2a55382bb889db53b5da5cdec5406c`.
- Central decision: `6da74892acd04b572dba1f7be338d5159eda5e52f0b132b1924e5a6e639bac57`;
  it grants only `simulation_training_ready` and withholds physical transfer
  and promotion.
- Runtime preflight: `860fabd7e4788fb6592aa57fe0d72d78b6ad53be2dc00173f2a9240447f95d46`.
- One-use permit: `7530e79db6b390d9bc5bca62f149f2a8e4ce9ca83b910faf622798d8edf555fa`.

All six reconstruct exactly from the reviewed T20.43 sources. Their tracked
file hashes are respectively `02096328...`, `eabb1211...`, `84d3f51e...`,
`96bce564...`, `4d153390...`, and `2e6f7f04...` in Gate A/owner/request/
decision/preflight/permit order.

## Pre-run findings

- The owner window is active from `2026-07-16T12:35:56-05:00` through
  `20:35:56-05:00`; this review occurred at 15:08 CDT.
- `2f2a2ca` is exact on the origin tracking ref and descends from reviewed
  implementation `9a03a86`. The complete implementation and authority scope
  has zero dirty paths and zero source drift.
- Gate A independently reconstructs the exact 129-episode/31,366-frame R0
  package, package/tree/order/features, training-only statistics, fixed sample
  tensors, processor/manual MEAN_STD parity, action inverse, held-out exclusion,
  and dataset-to-MuJoCo coordinate round trip without constructing a model.
- Runtime facts are Python 3.12.12, Torch 2.11.0, Torchvision 0.26.0,
  Datasets 4.8.5, MuJoCo 3.3.5, NumPy 2.2.6, Pillow 12.3.0, PyArrow 25.0.0,
  and package LeRobot 0.6.1. MPS is available; network and dependency fallback
  are disabled.
- Cached ResNet-18 bytes are exact at `f37072fd...` and 46,830,571 bytes.
  Free disk is 67,342,274,560 bytes, above the frozen 10-GiB floor.
- The acceptance, attempt marker, run root, checkpoint, rollout, mirror, run
  summary, result, scorecard, and retention paths are all absent and unaliased.
- The permit authorizes exactly one fresh ACT attempt with seed `20260801`,
  10,000 maximum updates, schedule `[0,500,1000,2500,5000,7500,10000]`,
  chunk-50 and receding-10 evaluation, and no retry, sweep, correction
  objective, threshold change, R2, external compute, or hardware action.

## Adversarial disposition

Source/cache/dependency/dataset/statistics/held-out/coordinate/commit drift,
dirty scoped files, stale authority, output collision or alias, schedule or
queue mutation, unsafe ACT defaults, non-finite optimization, trace/video
mismatch, first-pass replacement, retry, and authority escalation fail closed.
The immutable marker must be written before cached backbone tensor reading,
ACT construction, inference, or optimizer creation and consumes the sole
attempt even if a later operation fails.

## Authority granted

- Write and preserve the signed Reviewer 292 acceptance bound to this document,
  authority commit, and one-use permit.
- After that acceptance commit is exact on origin and the owner window remains
  active, create the sole permit-consuming marker and execute the fixed full
  ACT standard attempt once through all seven scheduled evaluations.
- Preserve the terminal success or negative result, all fourteen strict-v2
  traces and signed mirror manifests, scorecard, and retention receipt. The
  earliest pre-registered strict-v2 pass, if any, remains the selected Gate C
  evidence.

## Authority withheld

No second attempt, retry, resampling, sweep, correction objective, threshold
change, schedule change, checkpoint replacement, Gate B entry barrier, archive
replay, R2 activation, hardware/camera/serial access, physical motion, network
or download, external compute, Brev, physical transfer, promotion, destructive
operation, or learned-policy proof claim beyond the preserved simulation result.
