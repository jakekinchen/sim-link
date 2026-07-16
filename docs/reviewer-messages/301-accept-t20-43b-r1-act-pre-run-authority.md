# Reviewer Decision 301 - Accept T20.43b R1 ACT Pre-Run Authority

**Date:** 2026-07-16

## Decision

`ACCEPT_ONE_T20_43B_R1_ACT_REPLACEMENT_ATTEMPT`

Authority commit `5f8a31e373ca6133ddeee4ee788e244f10b19d3c` is exact on
`origin/codex/pi05-autolearn-loop`. The accepted implementation commit is
`5e8a2187bccd41377c53812487c8eeb299b41e54`, with machine-state synchronization
at required source commit `eb2aa9a3933988d3a5f29bcdc4a6758c99fb746e`.

## Reconstructed authority

- Stable renderer smoke: `35224058860ec408fea30e679ad0fdf440364d8ae38c5cb3412446b9c213cbd8`.
- Gate A: `ea65f3d1298b936e24c88f5c1e3810eb6cd6c93dc1bc8a088af6323748048798`.
- Owner grant: `09111fcb84dd5554f3d73c7964e94cda3028148c15f3c1e5cdb5789c4b95106f`.
- Central request: `fd13930fea534489ffb9294f3e2ac6467192dc417a170dea86d568fb2fd9da9d`.
- Central decision: `3b534f91daed81a67fb8d2ad211cdd42855939c58b4df1d153b11e2840e4395b`;
  it grants only `simulation_training_ready`.
- Runtime preflight: `549c0db2fa6ee525c02db38aa4f2e0dc566bf6d12a40c6b805905c53ae923df0`.
- One-use permit: `c7e8e1ca60007442cf7ec34cf5a56722b768c07d67585f82d8266c09d658f469`.

All seven reconstruct exactly. Their tracked file hashes are `20eab76b...`,
`f9588ec8...`, `52931258...`, `006b9eb6...`, `45063700...`, `fa1317d1...`,
and `e2ea74a3...` in smoke/Gate-A/owner/request/decision/runtime/permit order.

## Pre-run findings

- The owner window remains active through `2026-07-16T20:35:56-05:00`; this
  review occurred before the `19:50:56` no-new-major-slice cutoff.
- `5f8a31e` is exact on origin and descends from source `eb2aa9a` and accepted
  implementation `5e8a218`. The complete T20.43b implementation/authority
  scope has zero dirty paths.
- The fresh renderer smoke uses `external/lerobot/.venv/bin/python`, cached
  MuJoCo support tree `409f4ee7...`, MuJoCo 3.3.5, exact retained trace
  `6133ce58...` with file hash `f9dc0e6d...`, and emits a 745,243-byte MP4 plus
  signed manifest with exit 0.
- Gate A verifies exact 129-episode/31,366-frame R0, zero held-out training
  rows, 16 deterministic samples, exact processor/manual normalization,
  `3.8146973e-6` maximum action inverse error, and `1.4210855e-14` rad maximum
  coordinate round-trip error.
- MPS and all pinned dependency versions are present; the cached ACT backbone
  is 46,830,571 bytes with hash `f37072fd...`; fallback/network are closed; and
  preflight observed 59,424,571,392 free bytes.
- All eleven attempt/result/run paths were absent and unaliased. No marker,
  model construction/load/inference, optimizer, checkpoint, or rollout exists.

## Adversarial disposition

Interpreter/support-tree/cache/dependency/source/R0 drift, output collision or
alias, stale authority, recipe or schedule mutation, non-finite training,
queue/tail mistakes, strict-v2 evidence spoofing, retry, second replacement,
and authority escalation fail closed. Once written, the marker consumes the
sole replacement; every later exception must retain a signed terminal receipt.

## Authority granted

- Write and preserve the signed Reviewer 301 acceptance bound to this document,
  authority commit, and permit.
- After that acceptance is exact on origin and the owner window remains active,
  create the sole marker and execute the unchanged 10,000-update ACT campaign
  through all seven dual-semantics checkpoint evaluations once.
- Preserve the first strict-v2 pass if one occurs, or the exact terminal
  negative/failure, with complete trace, mirror, result, and retention evidence.

## Authority withheld

No second replacement, retry, sweep, recipe/schedule/threshold change,
correction objective, archive replay, T20.45 activation, package installation,
network/download, hardware/camera/serial access, physical motion, external
compute, Brev, transfer, promotion, or destructive operation.
