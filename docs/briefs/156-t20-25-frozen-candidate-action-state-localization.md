# Slice Brief 156 - T20.25 Frozen-Candidate Action/State Localization

**Date:** 2026-07-14

## Objective

Localize why the T20.17 clean-data and T20.24 recovery-augmented frozen PI0.5
adapters both fail before strict contact by comparing their requested actions
and visited simulator states against the exact held-out source trajectories.

## Contract

- Run no optimizer. Reverify both immutable training summaries, checkpoint
  trees, adapters, held-out source episodes, and prior negative result gates.
- Reproduce each frozen adapter on held-out seeds 6 and 7 with its declared
  inference seed, action horizon 5, no projection, no assistance, and the same
  244-frame strict-v2 simulator schedule.
- Capture all requested actions and pre-action MuJoCo states without mutating
  the source episodes or prior evaluation evidence.
- Compare each candidate with the exact source action and state at every
  schedule-aligned frame. Also compare the two candidates directly. Report
  frame-zero, pre-contact phase, per-phase, and per-joint errors plus the first
  action and state divergences.
- Treat frame-zero as identical-reset prediction evidence. Treat later
  comparisons as prediction plus compounding state-distribution drift; do not
  describe them as teacher-forced model loss.
- Use the measurements to select or reject one narrow next causal hypothesis.
  This slice may not allocate another optimizer rung or accept either policy.
- Do not access hardware or cameras, instantiate a physical robot, start
  external compute or Brev, change the twin, or consume Robo Scan evidence.

## Acceptance Criteria

- Tests reject missing/reordered seeds, candidates, frames, phases, or joints;
  non-finite values; source/checkpoint substitution; non-identical reset;
  projection/assistance; signed mutation; and authority escalation.
- All four candidate/seed runs account for 244 finite requested actions and
  states and preserve their exact source and checkpoint identities.
- A signed diagnostic gate reports the measured comparisons and explicitly
  separates identical-reset prediction error from later closed-loop drift.
- The gate identifies the earliest material divergence and records whether the
  recovery-augmented adapter improved, regressed, or left unchanged the
  source-relative frame-zero and pre-contact errors.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commits, and
  remote branch agree before T20.25 is described as verified.

## Out Of Scope

Teacher-forced image regeneration; additional training; checkpoint mutation;
dataset/statistics changes; reward weighting or RL; policy acceptance;
physical canary; hardware/camera access; twin calibration; Robo Scan; external
compute; or Brev.
