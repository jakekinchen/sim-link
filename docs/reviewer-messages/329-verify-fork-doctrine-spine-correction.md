# Reviewer Decision 329 - Verify Fork Doctrine Spine Correction

**Date:** 2026-07-17

## Decision

`VERIFY_K4_CORRECTED_FORK_DOCTRINE_SPINE_NO_NEW_AUTHORITY`

Brief 236 and implementation
`99c13d0392e7b911b9694f45d996d8f81531b877` reconcile the owner-approved
review corrections across the living fork spine. This is a documentation and
invariant-test result only; it executes no experiment and grants no authority.

## Verified technical anchors

- The pinned local LeRobot checkout is
  `e40b58a8dfa9e7b86918c374791599d070518d11`. Its normal dataset stack declares
  `CODEBASE_VERSION = "v3.0"`, and its native
  `src/lerobot/policies/groot/` integration consumes the standard dataset and
  processor surfaces. The living doctrine therefore tries native pinned-
  LeRobot GR00T first and reserves V3-to-V2 plus `modality.json` for standalone
  Isaac-GR00T.
- The pinned ACT configuration raises `ValueError` when `n_obs_steps != 1` at
  `src/lerobot/policies/act/configuration_act.py:148`. The two-to-four-step
  history rung is now an explicit wrapper/processor/model implementation slice,
  not a YAML edit.
- The compatibility gate names camera keys/order; action dimension/order/units
  and absolute-versus-relative semantics; gripper semantics; language fields;
  image size/aspect ratio; chunk horizon; normalization; and processor parity.

## Corrected execution doctrine

- The temporal ladder is F0c, a Markov-augmented state candidate, an explicit
  short state/action stack, then a small GRU/state Transformer only if needed.
  Simulation uses a velocity estimator reproducible on hardware rather than
  silently depending on exact simulator `qvel`.
- Correction episodes keep `terminal_failure_frame` separate from the earlier
  `causal_intervention_frame`, restore dynamics-relevant simulator state, and
  require the geometry expert to replan. Current one-observation ACT receives
  policy-induced corrective starts, not literal failed-prefix temporal context.
- PI0.5 remains the primary NVIDIA experiment and does not wait on GR00T.
  Native GR00T mapping/smoke/gateway work can overlap, but only one expensive
  VLA campaign trains on the lane at once; SmolVLA stays parked.
- `RUN_RECEIPT.json` is immutable and records parent/hypothesis/candidate/
  doctrine lineage plus a nullable evaluation reference. Promotion exists only
  in a separately signed evaluator-owned decision joined by `candidate_id`.
- The learned/scripted hybrid is the strongest simulation fallback and only a
  physical candidate after gateway, calibration, shadow mode, and a bounded
  canary. State primitives remain the reliable physical fallback until then.

## Same-agent adversarial review

The review removed three residual contradictions: the state path no longer
claims there is no sim2real gap at all; PI0.5 no longer waits for an end-to-end
demo or GR00T integration; and the architecture no longer depicts the evaluator
as the producer of the training receipt. ACT/state-RL remain the overall
demo-critical tracks while PI0.5 is primary specifically within the NVIDIA VLA
lane, so the priorities do not double-count or conflict.

The immutable `sim2claw-genesis` tag still resolves to `73dd45b...`. Frozen
`SOURCE_MANIFEST.json`, `source-selection.json`, and the signed F0c spec have no
diff. The correction adds no training entrypoint, schema mutation, dataset
conversion, package install, network access, model action, rollout, hardware,
external compute, Brev operation, transfer, promotion, or destructive action.
Pre-existing `.codex/config.toml`, external checkouts, and `tmp/` remain
unrelated and unstaged.

## Verification

- 14 reconstruction-kit tests pass in 91.210 seconds, including the new
  corrected-doctrine invariant.
- 21 documentation-information-architecture and project-state-pointer tests
  pass.
- Frozen manifest generation check returns `ec9084dc...` unchanged.
- Strict JSON parsing, local link resolution, forbidden-stale-phrase search,
  and `git diff --check` pass.

## Disposition

K4 is verified and closed. The living post-tag doctrine now records the exact
revision each future run must cite. The source tag, F0c package, training lock,
hardware gates, and current fork-native execution requirements remain
unchanged.
