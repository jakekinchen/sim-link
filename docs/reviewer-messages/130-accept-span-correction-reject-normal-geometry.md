# Reviewer Decision 130 - Accept Span Correction, Reject Normal Geometry

**Date:** 2026-07-13

## Decision

`CONTINUE - ACCEPT SPAN CORRECTION; REJECT NORMAL GEOMETRY`

Fresh review checked projection sign, accidental vertical-offset removal,
selected-axis label drift, re-solve omission, candidate or holdout substitution,
contact-physics tuning, legacy artifact drift, unilateral/bilateral
conflation, span-only strict acceptance, normal sign handling, strict-v2
fabrication, grasp overclaim, and authority escalation.

Selected-axis centering causally improves representative span, including one
candidate above the strict minimum, while leaving normal alignment far below
threshold and bilateral-candidate motion invalid. Only
`selected_axis_centering_span_correction_observed` and repeatable bilateral
contact are accepted. Geometry eligibility, unassisted MuJoCo grasp, training
readiness, and physical actuation remain withheld.

The next slice must audit actual contact points, object faces, and inward
normals in object frame before changing pose or contact geometry again.
