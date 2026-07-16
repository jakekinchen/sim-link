# Reviewer Decision 296 - Accept T20.44 R2 SmolVLA Pre-Run Authority

**Date:** 2026-07-16

## Decision

`ACCEPT_ONE_T20_44_R2_SMOLVLA_STANDARD_ATTEMPT`

Authority commit `37ae58163d054d2a4188f6cd272c3c8a2188d0c8` is exact
on `origin/codex/pi05-autolearn-loop`. The corrected implementation commit is
`e79a5c7dfbf6407e5908e0a2656f7afdc4f14ef0`.

## Reconstructed authority

- Stable renderer smoke: `11cbcca31a546b100acd92e173a8cb68c57c27cf6c20485c67be7fb1b2c7cc35`.
- Gate A: `ef79292d7f4120012d0c6f492966052fb106594551fb7f07ad77f091ba7f15af`.
- Owner grant: `6cc7f650f5454d25a4c15c849cfbc338384b4d81b54fefd30eb067af7e0483fb`.
- Central request: `4a5163c1ce766179803fbfabc782e02732a92306ada6ec751a47c399996aedec`.
- Central decision: `f9e817c4d9fdec94b73186ac797161a75d7b937390204f1d8f3bc6bc7008d318`;
  it grants only `simulation_training_ready`.
- Runtime preflight: `7a3231a35b222e64dc67658188457e5e0a67036f69bbf5a39eb13205b3361cc6`.
- One-use permit: `5301aa32a809e2350d1ddb2c4c335d9a437d3fec4c460fb6a6aba45d3d2145e9`.

All seven reconstruct exactly. Their tracked file hashes are `88f55972...`,
`00b6b0ca...`, `1f0e11e7...`, `586334d7...`, `f151c0b6...`, `e53fc9fe...`,
and `dae0ac2a...` in smoke/Gate-A/owner/request/decision/runtime/permit order.

## Pre-run findings

- The owner window remains active through `2026-07-16T20:35:56-05:00`; this
  review occurred at 15:55 CDT.
- `37ae581` is exact on origin and descends from corrected implementation
  `e79a5c7`. The complete implementation/authority scope has zero dirty paths.
- The stable renderer smoke uses
  `external/lerobot/.venv/bin/python`, bound cached MuJoCo support tree
  `409f4ee7...`, MuJoCo 3.3.5, exact trace `6133ce58...`, and produces a
  745,243-byte MP4 plus signed manifest with exit 0.
- Gate A verifies exact 129-episode/31,366-frame R0, training-only statistics,
  held-out exclusion, SmolVLA tokens/processors, zero manual normalization
  error, `3.8146973e-6` action inverse error, and `1.4210855e-14` rad coordinate
  round-trip error.
- Policy/VLM raw-byte hashes are exact (`7cd549ac...` / `b9bfd456...`), snapshot
  tree identities are `b35e9957...` / `0dfbc547...`, MPS is available, every
  dependency version is exact, fallback/network are off, and free disk is
  66,817,105,920 bytes.
- All eleven run/failure output paths are absent and unaliased. No marker,
  tensor deserialization, model, inference, optimizer, checkpoint, or policy
  rollout exists.

## Adversarial disposition

Temporary or mismatched interpreter, support-tree/cache/dependency/source/R0/
held-out drift, output collision or alias, stale authority, unsafe trainable
scope, scheduler mutation, non-finite training, decode-seed drift, queue/tail
errors, strict-v2 spoofing, trace/video mismatch, first-pass replacement,
retry, and authority escalation fail closed. Once written, the marker consumes
the sole attempt; every later exception must retain a signed terminal receipt.

## Authority granted

- Write and preserve the signed Reviewer 296 acceptance bound to this document,
  authority commit, and permit.
- After that acceptance is exact on origin and the owner window remains active,
  create the sole marker and run the fixed 5,000-update cached-base SmolVLA
  attempt through all five dual-semantics evaluations once.
- Preserve the first strict-v2 pass if one occurs, or the exact terminal
  negative/failure, with complete trace/mirror/result evidence.

## Authority withheld

No second attempt, retry, replacement, package installation, network/download,
correction objective, Gate B barrier, threshold/schedule change, checkpoint
replacement, archive replay, T20.45, hardware/camera/serial access, physical
motion, external compute, Brev, transfer, promotion, or destructive operation.
