# Reviewer Decision 126 - Accept Motion Separation, Reject Strict Geometry

**Date:** 2026-07-13

## Decision

`CONTINUE - ACCEPT MOTION SEPARATION; REJECT STRICT GEOMETRY`

Fresh review checked legacy signed-artifact drift, settle-duration ambiguity,
passive/gripper motion conflation, candidate or holdout substitution,
friction/range tuning, contact double counting, short-span acceptance, normal
sign errors, strict-v2 fabrication, grasp overclaim, and authority escalation.

The first focused run correctly rejected a compatibility defect that added new
fields to legacy no-settle artifacts. The corrected implementation scopes all
new diagnostics to the explicit post-yaw-settle path, and the legacy artifacts
remain byte-identical.

Only `passive_yaw_settle_motion_separated` and
`approach_motion_gate_valid_candidates_observed` are accepted. Contact geometry
still fails the existing 20 mm span and 0.8 alignment thresholds; geometry
eligibility, unassisted MuJoCo grasp, training readiness, and physical
actuation remain withheld. The next isolated correction is compiled
closing-axis/principal-axis alignment without contact-physics tuning.
