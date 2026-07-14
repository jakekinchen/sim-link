# Slice Brief 154 - T20.23 Recovery-Augmented Dataset Preflight

**Date:** 2026-07-14

## Objective

Freeze and materialize one source-bound LeRobotDataset that combines the six
verified T20.17 nominal strict-success episodes with only the four verified
T20.18 strict-success recovery branches, while retaining the two near-failure
and two failure branches outside training as immutable diagnostics.

## Contract

- Reverify the complete T20.17 source store and T20.18 recovery package before
  selecting any frame. Bind every selected episode, image, state, measured
  action, source record, outcome, and generation reason by content identity.
- Include all six nominal training episodes and exactly the four T20.18
  `recovery` episodes. Do not include near-failure or failure outcomes in
  behavioral-cloning statistics or training rows.
- Preserve T20.17 seeds 6-7 and all excluded T20.18 branches outside the
  materialized dataset and its statistics. Record them as evaluation-only
  references, not as rejected or relabelled successes.
- Use the package LeRobotDataset implementation and the same two camera keys,
  six-joint state/action schema, task prompt, 30 Hz rate, measured-action
  convention, and clean content-addressed `lerobot/pi05_base` snapshot as
  T20.17. No padding, inferred actions, image reuse, or source mutation.
- Freeze exact source-class episode and frame counts. No implicit resampling or
  duplicated episodes; any later weighting must be a separately declared
  training contract.
- This preflight may materialize and verify the dataset and compose a central
  simulation-only training decision. It may not load a model, run inference or
  an optimizer, execute a rollout, access hardware or cameras, start external
  compute or Brev, or grant policy acceptance, physical transfer, or promotion.

## Acceptance Criteria

- Tests first reject source drift, duplicate/unknown branches, non-recovery
  training outcomes, diagnostic leakage, bad image paths or hashes, non-finite
  state/action values, schema mismatch, padded/inferred actions, held-out
  leakage, statistics drift, signed mutation, and authority escalation.
- The actual persistent dataset contains 10 episodes and 2,330 frames: 1,464
  nominal frames plus 866 recovery frames. Its manifest and quantile statistics
  are reproducible from verified immutable sources.
- A signed mixture/training specification binds exact source memberships,
  exclusions, dataset manifest/statistics, processor-facing schema, clean model
  snapshot, and a bounded future campaign while keeping execution fields false.
- Only the central authority composer may grant `simulation_training_ready`,
  and it must withhold every physical, transfer, promotion, external-compute,
  and Brev decision.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commit, and
  remote branch agree before T20.23 is described as verified.

## Out Of Scope

Optimizer execution; checkpoint creation; policy evaluation or acceptance;
failure/near-failure imitation; reward weighting; implicit oversampling;
posterior calibration; Robo Scan ingestion; hardware or camera access; live
robot execution; physical transfer or promotion; external compute; or Brev.
