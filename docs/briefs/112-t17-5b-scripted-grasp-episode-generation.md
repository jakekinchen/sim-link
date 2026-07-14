# Slice Brief 112 - T17.5b Scripted Grasp Episode Generation

**Date:** 2026-07-13

## Objective

Re-run the verified T19.0l geometry-derived unilateral grasp as a deterministic
recording scripted expert. Emit eight immutable, content-addressed raw rollout
records with complete per-frame evidence and a fresh non-empty T17.4-path
compiled view, without training or physical authority.

## Contract

- First extend T17.4/T17.5 action completeness narrowly: `observed` is valid;
  `derived` is valid only with six finite values, exact named joint order, and
  provenance whose `state` is `derived` with a nonblank derivation. All other
  states remain quarantined/rejected. Derived values must never be relabeled.
- Store raw bytes append-only under ignored
  `outputs/robot_lab/t17_5b_raw_store`; commit only a signed manifest with
  byte hashes, source identities, fixed seed/config identities, counts, and
  outcomes. Re-running the same generation must reproduce that manifest.
- Seed 0 replays the exact T19.0l request and must retain the original strict
  full-cycle gates: 8/8 grasp hold, 24/24 lift, 12/12 unsupported hold, and
  24/24 lower. The other seven fixed seeds apply only documented +/-1 mm
  planar scene offsets and +/-0.03 rad yaw; every per-seed grasp target and
  aperture is re-derived by the existing geometry path. Any failure remains a
  signed retained outcome with measured-vs-threshold margins.
- Every frame retains requested, proposed, projected, sent, and measured
  actions; requested/achieved gripper poses; simulator actuator effort;
  six-joint position/velocity data; exact simulator timestamp; and top/wrist
  256px PNG observations. By-construction equal variants are `derived` with a
  named derivation, not absent.
- Declare `rollout_start`, phase changes, scene changes, resets, and
  `rollout_end` as hard boundaries. Retain 64 unassisted stable-hold frames in
  each rollout so horizon-50 windows can exist entirely within one declared
  phase; never cross or pad boundaries.
- Compile a new output directory via the existing frame/segment compiler,
  preserving the verified Brief 110/111 outputs. The new view must have >0
  eligible frames and >0 hard-boundary segments. It does not grant training.
- Store 3-5 top/wrist rendered keyframes for seed 0 and every distinct failure
  class in the signed generation manifest.

## Acceptance Criteria

- Deterministic rerun yields byte-identical signed store manifest; raw bytes
  are append-only and all hash references resolve beneath the declared root.
- All raw/frame records pass the T17.1 validators; complete action evidence
  has no availability downgrade. Tests reject derived actions without named
  derivation, invalid values, implicit missing variants, boundary crossing,
  source/hash drift, or authority escalation.
- The fresh compiler view has nonzero eligible frames and segments, and the
  reason-1/2/3 evidence gaps are absent for every retained generated frame.
- Seed 0 strict success and 3-5 rendered proof keyframes are present. Other
  seeds report configured/realized counts, terminal outcomes, strict success,
  and every failed gate's measured/threshold margin truthfully.

## Expected Files

- generator, raw-store verifier, and focused tests
- T17.4/T17.5 derived-action compatibility updates and regression tests
- `configurations/robot_lab/t17_5b_episode_generation_manifest.json`
- `configurations/robot_lab/t17_5b_compile/`
- workflow state, ledger, session, and reviewer evidence

## Out Of Scope

No dataset mixture, optimizer, training, policy learning, Brev, external
compute, hardware, physical motion, object-count expansion, source rewriting,
or relabeling of failures.

## Stop Conditions

Stop if seed 0 cannot repeat the verified strict cycle, if a source record
needs inference or padding, if a raw hash cannot be reproduced, or if the
renderer cannot emit valid 256px top/wrist proof keyframes. Retain truthful
failed-episode evidence but never call it an eligible success.

## Verified Outcome

- Implementation commit `5c3c34bbd9676e0b03015c17d249ed5e30c765d8` adds the
  append-only recorder, named-derived action validation, deterministic writer,
  and focused coverage. Evidence commit
  `8ccee812af3d8dfe899ecc7876ba0ead300a680d` preserves only the signed
  manifest and its compiler/window views; raw bytes remain ignored and
  append-only.
- All eight fixed seeds replayed as strict successes. Seed 0 retains the
  original 8/24/12/24 strict counts, adds 64 unassisted recording-hold frames,
  and retains five 256px top/wrist proof keyframes at pregrasp, close,
  grasp-hold, unsupported-lift-hold, and retreat.
- The signed episode manifest identity is
  `3860158e201e457146a167cfa778da14f210d88fa223cb075a1ec6d422ecfd1a`.
  The fresh compiler has 1,952 eligible frames, 88 hard-boundary segments, and
  zero quarantines. The unpadded window view contains 1,600/1,176/848/120
  windows at horizons 5/10/15/50, respectively.
- The 15-test focused compiler/window/episode suite and the 68-test relevant
  regression set passed. Existing T17.4 and T17.5 writers remained
  byte-identical, and a fresh eight-seed temporary replay reproduced the signed
  store manifest, compiler output, and window output byte-for-byte. No
  training, optimizer, hardware, Brev, physical, or raw-rewrite authority was
  granted.
