# Reviewer Decision 127 - Accept Axis Alignment, Reject Bilateral Contact

**Date:** 2026-07-13

## Decision

`CONTINUE - ACCEPT COMPILED AXIS ALIGNMENT; REJECT BILATERAL CONTACT`

Fresh review checked invented-threshold drift, axis sign ambiguity,
object-frame/world-frame confusion, unreachable-candidate acceptance,
candidate or holdout substitution, friction/range tuning, legacy artifact
drift, unilateral/bilateral conflation, strict-v2 fabrication, grasp overclaim,
and authority escalation.

The provisional 0.95 gate was correctly rejected and replaced by the existing
strict-v2 0.8 threshold. Four candidates mechanically meet it, but all retain a
large vertical closing-axis component and none reaches the moving pad. Only
`compiled_principal_axis_wrist_roll_alignment_observed` is accepted. Bilateral
contact, geometry eligibility, unassisted MuJoCo grasp, training readiness, and
physical actuation remain withheld.

The next isolated correction is a bounded joint wrist-flex/wrist-roll solve for
a horizontal principal-axis closing vector, with contact physics unchanged.
