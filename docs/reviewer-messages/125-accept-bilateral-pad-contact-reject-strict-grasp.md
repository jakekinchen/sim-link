# Reviewer Decision 125 - Accept Bilateral Pad Contact, Reject Strict Grasp

**Date:** 2026-07-13

## Decision

`CONTINUE - ACCEPT BILATERAL PAD CONTACT; REJECT STRICT GRASP`

Fresh review checked pad-reference aliasing, candidate or holdout substitution,
unilateral/bilateral conflation, zero-force counting, representative-contact
double counting, normal reversal, short-span acceptance, preclose baseline
drift, friction or range tuning, strict-v2 fabrication, grasp overclaim, and
authority escalation.

Two candidates retain bilateral explicit-pad contact through every hold frame,
but their contact spans and inward-normal alignment produce zero strict-v2
valid frames. Both also exceed the preclose object-motion limit. Only
`bilateral_explicit_pad_contact_observed` is accepted. Geometry eligibility,
unassisted MuJoCo grasp, training readiness, and physical actuation remain
withheld.

The next causal correction is to let object yaw settle deterministically on the
table before defining the approach-motion baseline. Search design, contact
physics, ranges, evaluator, and holdout must stay unchanged.
