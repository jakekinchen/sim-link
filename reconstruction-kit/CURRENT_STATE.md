# Current Proof State

Snapshot source: `sim-link` commit
`6c53d9309f7f41f0d3ac351c049436ddda20e50f` on
`codex/pi05-autolearn-loop`, recorded 2026-07-16.

## Operational verdict

| Layer | State | Exact meaning |
| --- | --- | --- |
| Constructive simulation source | Verified | Deterministic geometry-derived controller produces strict-v2 grasp/lift episodes under the bounded R0 construction space. |
| Dataset and processor | Verified | R0 has 129 training episodes, 31,366 frames, 59,904 windows, training-only MEAN_STD statistics, and zero held-out rows admitted to training. |
| Evidence and authority | Verified | Canonical JSON/SHA-256, source identities, central composition, renderer smoke, trace mirroring, and one-use permits fail closed. |
| SmolVLA learned policy | Verified terminal negative | One 5,000-update, five-checkpoint, ten-rollout campaign produced no Gate C pass. |
| ACT learned policy | Unresolved and unconsumed | The stable-runtime 10,000-update replacement is implemented and pre-run accepted, but no marker/model/optimizer/rollout exists. |
| PI0.5 learned policy | Negative diagnostic history | Extensive Gate B work localized structured decode/objective mismatch; no learned Gate C success exists. |
| Physical twin/transfer | Not qualified | Physical calibration, metric Robo Scan handoff, task proof, transfer, and promotion remain open. |

## Verified R0 source package

- Result identity: `d238379bce62d884833da0a449535e3dc24f988b8da573513ae684bbb19a5969`.
- 119/119 newly generated training episodes pass strict-v2.
- 9/9 fresh held-out episodes pass strict-v2 and remain excluded from training.
- Exact T20.23 base is included once, producing 129 training episodes total.
- 31,366 training frames and 59,904 indexed windows.
- Mixture identity: `37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df`.
- Statistics identity: `02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae`.

This proves source behavior and dataset construction, not learned-policy
competence.

## SmolVLA result

- Result identity: `9d916206cbbb86b67a42d3449953bc7b272e1de5171996df224e29772369e14f`.
- Training: 5,000 finite MPS updates.
- Evaluation: checkpoints 0, 500, 1,000, 2,500, and 5,000 under chunk-50 and
  receding-10 semantics; ten strict-v2 rollouts total.
- Outcome: zero Gate C passes and no selected checkpoint.
- Strongest partial: checkpoint 1,000/receding-10, 73 strict-contact frames,
  18.061304 mm lift, still below the unchanged 25 mm/phase-duration gate.
- Retry/replacement: closed.

This is a clean model result, not an infrastructure failure.

## ACT boundary

- Spec identity: `13c5bb4b2cadf8c451a25e7c11e9e0a1d824468f593774fdb60dbf7fa5197461`.
- Fixed recipe: ACT, batch 8, training seed 20260801, AdamW at `1e-5`, no
  scheduler, 10,000 updates, checkpoints 0/500/1,000/2,500/5,000/7,500/10,000,
  chunk-50 and receding-10 evaluation.
- Stable renderer smoke: `35224058860ec408fea30e679ad0fdf440364d8ae38c5cb3412446b9c213cbd8`.
- Gate A: `ea65f3d1298b936e24c88f5c1e3810eb6cd6c93dc1bc8a088af6323748048798`.
- Pre-run acceptance: `525de8dc417d9522c94573d4b781e8631126c9346029c961821eedbf9b1af772`.
- Marker, model, optimizer, checkpoint, rollout, and result: absent.

The old owner window and permit are historical and expired. The attempt remains
unconsumed; a new repository must create a fresh administrative authority epoch
and must not treat that refresh as a second replacement.

## Claims that remain false

- `learned_policy_strict_v2_success`
- `physical_twin_qualified`
- `physical_transfer_ready`
- `promotion_eligible`
- `hardware_authorized`
- `external_compute_authorized`
- `brev_compute_authorized`

See `CURRENT_STATE.json` for the same boundary in machine-readable form.
