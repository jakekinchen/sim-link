# Slice Brief 150 - T20.19 Discrete Recovery Ensemble V0

**Date:** 2026-07-14

## Objective

Falsify the verified T20.18 approach-phase measured-action recovery controller
against one fixed, physically bounded 12-cell MuJoCo ensemble and preserve a
nominal/worst-cell strict-v2 scorecard without inferring a calibrated posterior.

## Contract

- Bind T20.18 causal manifest
  `f97c784f2f68ce3028a221acb715576c8c3fcaf0e66917e77ad28ecef11dd0b3`,
  episode package
  `4123e8d40e5e1fd80702c4dc40ceb7a31922c2da2f36c797c91a20677f208e7c`,
  and the strict approach-nominal recovery branch
  `35790636312237b8b067a56ba5979e571b970845c309bedf2ab559106bc276d0`.
- Define exactly 12 immutable cells: nominal; cube x and y offsets at plus or
  minus 4 mm; object friction multipliers 0.8 and 1.2; command delays of one and
  two frames; a two-frame action hold; and gripper-command scales 0.95 and 1.05.
  Change only one named factor outside the nominal cell.
- Restore the exact policy-visited parent integration state for every cell, use
  seed 6, and apply the same measured source-action suffix. Any delay or hold
  transformation must be explicit, deterministic, fixed-length, and
  content-bound; it cannot be relabelled as a measured source sequence.
- Prove every pose, friction, timing, hold, and gripper bound is finite and
  physically valid before simulation. Reject control projection, missing or
  duplicate cells, factor interaction, path aliasing, source drift, and output
  overwrite.
- Run every cell twice and require exact state/action/contact/result replay.
  Record all strict-v2 gates, nominal outcome, per-cell outcome, success rate,
  and the deterministic worst-cell ordering. A robust or fragile result is
  evidence about this discrete grid only, not a posterior over the real world.
- Do not run an optimizer, mutate the T20.18 episode package, access hardware or
  cameras, start external compute or Brev, or grant training readiness, policy
  acceptance, physical transfer, or promotion.

## Acceptance Criteria

- Tests first cover the exact 12-cell manifest, one-factor-only rule, finite and
  physical bounds, fixed-length delay/hold transforms, gripper scaling,
  deterministic ordering, duplicate/alias rejection, replay drift, scorecard
  derivation, and authority escalation.
- All 12 cells restore the same bound parent and execute the same source-bound
  controller under only their declared intervention; every second replay is
  byte-identical to its first.
- A signed scorecard reports nominal and worst-cell strict-v2 outcomes and
  explicitly states that the grid is discrete and uncalibrated.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commit, and
  remote branch agree before T20.19 is described as verified.

## Out Of Scope

BayesSim, ASID, posterior inference or calibration; factor interactions;
learned residual dynamics; visual/object/task-family randomization; optimizer
training; dataset mixture freeze; T20.20-T20.22; hardware or camera access;
physical transfer; promotion; external compute; or Brev.
