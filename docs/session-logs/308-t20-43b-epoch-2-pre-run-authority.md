# Session Log 308 - T20.43b Epoch-2 Pre-Run Authority

**Date:** 2026-07-16

## Scope

Materialize, reconstruct, adversarially review, and accept one fresh
administrative authority epoch for the unchanged T20.43b ACT replacement. No
attempt marker, model, optimizer, checkpoint, rollout, or Gate C action was
permitted in this boundary.

## Verified repository boundary

- Branch: `codex/pi05-autolearn-loop`.
- Reviewed implementation/state boundary: `677b65cd9fe222916a7f0e802b102e7e24c602e0`.
- Materialized-authority commit: `1012028ba4265b12457b83d721df2d9c5c1ab027`.
- Local HEAD and `origin/codex/pi05-autolearn-loop` were exact at the authority
  commit before acceptance was written.
- Unrelated Codex configuration, K1 reconciliation, external-source, and
  temporary dirt remained preserved and outside the scoped boundary.

## Epoch-2 authority

The owner window is `2026-07-16T21:25:04-05:00` through
`2026-07-17T05:25:04-05:00`. Epoch 2 retains replacement ordinal 1, attempt
ordinal 1, one authorized attempt, and no retry.

| Artifact | Identity SHA-256 | File SHA-256 |
| --- | --- | --- |
| Owner authorization | `fe05f0d2654c19aeea14b19ef5069db570c7a1fa72a326d07fa7e0951ec9a9b4` | `e7816d9aba9fc0e006d5075df8359dcb89386c84f286e256a09ad3a9be563ea0` |
| Central request | `21ebdab15c46d751074656b70b8f9b845288976792a1d8af6c513601c0cd8a1b` | `81f7ef785ac031676192e37471237122f78849a26ee5ec48b9903379bc67fef6` |
| Central decision | `061b1c1b51df7a044f014e3ec951e79fc7342cf0d6883f157b04dbc0201e4ce7` | `510ff0e26eb420fe7d1ca358c6f1f17ece6dc38548f12b1318055c305e0dd7e3` |
| Runtime preflight | `edd06509dae01d14268dee306f356d1802bea1a3cb7bd215acf77a0924f960ae` | `02ef603d31cea29a05401b05913a3be6d7f9edba4489edc62dd89b3ba4f065ed` |
| One-use permit | `81b38484dddf8ff565b4ff12ba3ef4303c6ad8629b97119df717c0347ece55b8` | `4d0c66e0492b6ec4f616cccb7f9c07c8d4908d6ded67d70dee99cc20b9f76c05` |

The central composer grants only `simulation_training_ready`. MPS, the exact
offline dependency set, cached ResNet-18, MuJoCo 3.3.5 support tree, origin
ancestry, clean scoped implementation paths, and absence/unaliased state of
all marker/run/result paths reconstruct exactly.

## Acceptance

- Reviewer decision: `305`,
  `ACCEPT_T20_43B_EPOCH_2_ATTEMPT_1`.
- Acceptance identity:
  `c6af103096710491a7ec9f1439b349e0d9bca7033a2709ba367ebc1d786127c7`.
- Acceptance file SHA-256:
  `c3ee9e56a266329f828f723d4f280bc63b12aa9185847e314ada68f3f8a5f6b1`.
- Acceptance is bound to permit `81b38484...`, authority commit `1012028...`,
  and the exact Reviewer 305 file SHA.

Both the five authority artifacts and acceptance independently verify. The
sole marker remains absent. After this acceptance boundary is exact on origin
and the window remains active, the fixed 10,000-update/14-rollout runner may
consume the one attempt exactly once.

## Authority still closed

No retry, second replacement, recipe/schedule/threshold change, correction
objective, archive replay, T20.45 activation, hardware, camera, serial,
physical motion, network, package installation, external compute, Brev,
transfer, promotion, or destructive action is authorized.
