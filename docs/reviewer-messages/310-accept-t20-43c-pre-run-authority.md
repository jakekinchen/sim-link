# Reviewer Decision 310 - Accept T20.43c Pre-Run Authority

**Date:** 2026-07-16

## Decision

`ACCEPT_ONE_T20_43C_ZERO_UPDATE_ACT_CONTINUATION`

Authority commit `02496f0eb9f09b4d84d06750143ddf06d202592a` is exact on
`origin/codex/pi05-autolearn-loop` and descends from reviewed recovery boundary
`ca9b9ccbdbb22e49e566e1b4f81076dfbfac29fd`.

## Reconstructed authority

- Actual-schema smoke `9e8783dc...`, file SHA `1c53c4ee...`; it binds unchanged
  MP4 SHA `955ad918...`, signed manifest `00494310...`, and truthfully records
  the post-render administrative recovery.
- Owner grant `315aef82...`, file SHA `e390b6d6...`.
- Central request `bf53bcc0...`, file SHA `7faccad9...`.
- Central decision `c316bf01...`, file SHA `313f88ee...`; it grants exactly
  `simulation_training_ready`.
- Runtime preflight `8d4fbf89...`, file SHA `aeff6cdb...`.
- One-use permit `166a6cd0...`, file SHA `1040cbf9...`.

All six artifacts reconstruct through the reviewed live verifier. The owner
interval is `2026-07-16T22:12:13-05:00` through
`2026-07-17T06:02:13-05:00`.

## Pre-run findings

- T20.43b terminal receipt `89b6dbff...`, source marker `d67cf38...`,
  checkpoint `916200d0...` / model file `acc865fb...`, and trace `b707b815...`
  reconstruct without mutation.
- Required source `ca9b9cc...` and authority commit `02496f0...` are on origin.
  T20.43c implementation paths are clean despite unrelated preserved worktree
  dirt.
- Exact Python 3.12 / torch / torchvision / datasets / MuJoCo / NumPy / Pillow /
  PyArrow / LeRobot pins pass; MPS is available; 35,799,519,232 free bytes were
  observed; network use is false.
- Acceptance, marker, continuation run root, equivalence, result, scorecard,
  retention, terminal-failure, and final-receipt paths were absent and
  unaliased at preflight.
- No checkpoint tensor read, model construction/load/inference, optimizer,
  rollout, or Gate C action has occurred.

## Adversarial disposition

Source-tree mutation, smoke spoofing, stale origin, implementation drift,
output alias/collision, non-finite result encoding, authority escalation,
retry/replacement, recipe/schedule/threshold mutation, and
hardware/network/external/Brev authority fail closed. The marker consumes the
sole continuation before any checkpoint tensor or model action; update 1 is
additionally barred until bit-exact fresh-ACT/checkpoint equality, empty AdamW
state, and zero consumed batches are signed.

## Authority granted

- Write one signed acceptance bound to this decision, permit, and authority
  commit.
- After the acceptance and this decision are exact on origin and the window is
  active, create the sole continuation marker.
- Prove the zero-update equivalence receipt, then execute the unchanged ACT
  updates 1-10,000 and fixed seven-checkpoint dual-semantics evaluations once.
- Preserve either the first strict-v2 Gate C pass or the exact terminal
  negative/failure with complete local evidence and compact signed receipts.

## Authority withheld

No retry, second continuation, fresh replacement, sweep,
recipe/schedule/threshold/dataset change, correction objective, archive replay,
T20.45 activation, hardware, camera, serial, physical motion, network, package
installation, external compute, Brev, transfer, promotion, or destructive
operation.
