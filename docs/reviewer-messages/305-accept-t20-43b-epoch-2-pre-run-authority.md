# Reviewer Decision 305 - Accept T20.43b Epoch-2 Pre-Run Authority

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43B_EPOCH_2_ATTEMPT_1`

Authority commit `1012028ba4265b12457b83d721df2d9c5c1ab027` is exact on
`origin/codex/pi05-autolearn-loop` and descends from the reviewed implementation
and synchronized-state boundary `677b65c`.

## Reconstructed epoch-2 authority

- Owner grant `fe05f0d2...`, file SHA `e7816d9a...`.
- Central request `21ebdab1...`, file SHA `81f7ef78...`.
- Central decision `061b1c1b...`, file SHA `510ff0e2...`; it grants only
  `simulation_training_ready`.
- Runtime preflight `edd06509...`, file SHA `02ef603d...`.
- Permit `81b38484...`, file SHA `4d0c66e0...`.

All five reconstruct exactly through the reviewed epoch-2 verifier. The owner
interval is `2026-07-16T21:25:04-05:00` through
`2026-07-17T05:25:04-05:00`, exactly 28,800 seconds.

## Pre-run findings

- Epoch 1 reconstructs at its original identities and file hashes; no epoch-1
  path was rewritten.
- Epoch 2 fixes refresh 2, replacement ordinal 1, attempt ordinal 1, one
  authorized attempt, and no retry or sweep.
- Required source `677b65c` and authority commit `1012028` are on origin. The
  epoch-2 implementation scope has zero dirty paths despite unrelated preserved
  Codex, K1 reconciliation, external, and temporary dirt elsewhere.
- Exact dependencies pass; MPS is available; the cached ResNet-18 and MuJoCo
  3.3.5 support tree match; 37,918,679,040 free bytes were observed.
- The sole marker, run root, checkpoint, rollout, mirror, summary, result,
  scorecard, retention, and terminal-failure paths are absent and unaliased.
- No backbone tensor, model construction/load/inference, optimizer, checkpoint,
  rollout, or Gate C action has occurred.

## Adversarial disposition

Stale epoch reuse, base-byte drift, source/runtime/cache drift, marker/output
collision, path aliasing, authority escalation, second replacement or attempt,
retry, recipe/schedule/threshold mutation, and hardware/network/external/Brev
authority fail closed. The marker remains exclusive and consumes the sole
attempt before any model or optimizer action.

## Authority granted

- Write the signed epoch-2 acceptance bound to this reviewer decision, permit,
  and authority commit.
- After that acceptance and this decision are exact on origin and the owner
  interval remains active, create the sole marker and execute the unchanged
  10,000-update ACT campaign through all seven dual-semantics evaluations once.
- Preserve either the first strict-v2 Gate C pass or the exact terminal
  negative/failure with complete local checkpoint/trace/mirror evidence and
  compact signed result/scorecard/retention artifacts.

## Authority withheld

No second replacement, retry, continuation, sweep, recipe/schedule/threshold
change, correction objective, archive replay, T20.45 activation, hardware,
camera, serial, physical motion, network, package installation, external
compute, Brev, transfer, promotion, or destructive operation.
