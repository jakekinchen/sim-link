# Slice Brief 130 - T20.10 Release-Semantics Reconciliation

**Date:** 2026-07-14

## Objective

Reconcile the policy closed-loop release gate with T20.6 strict semantics by
distinguishing active force-bearing fingertip/non-pad contact from a zero-force
collision pair, while retaining final geometric retreat clearance.

## Contract

- Preserve historical T20.7 and T20.9 byte reproducibility through an explicit
  legacy geometry-pair release mode; do not silently reinterpret signed past
  artifacts.
- Add a named force-bearing release mode in which the final release-settle frame
  passes only when no positive pad aggregate and no non-pad robot/object contact
  remains. Keep the final retreat gate based on complete geometric contact-pair
  clearance.
- Emit a new T20.10 source-bound oracle result from the same immutable seed-2
  actions, exact policy adapter, 244-frame schedule, five 256 px keyframes, and
  measured gate margins. The corrected semantic basis must be explicit in the
  signed output.
- Require all T20.9 zero-divergence checks to remain true. A trajectory change,
  action projection, assistance, missing keyframe, or newly failed strict gate
  fails the correction.

## Acceptance Criteria

- The legacy T20.9 output still verifies byte-identically under its original
  geometry-pair semantics.
- The new oracle records release active-contact clear `1/1`, retreat geometry
  clear `1/1`, 36+ mm lift, every strict gate passed, and strict success without
  model load, inference, optimizer work, or a policy-acceptance claim.
- Tests reject mode confusion, force-bearing pad or non-pad contact at release,
  missing retreat clearance, source/action/state drift, and re-signed authority
  escalation.
- Same-agent review checks semantic weakening, historical reinterpretation,
  contact-force omission, false model success, and contradictions with T20.6.

## Out Of Scope

Changing source actions, retraining, model inference, policy acceptance,
residual RL, hardware, physical transfer, promotion, external compute, and
Brev.
