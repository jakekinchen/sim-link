# Reviewer Decision 118 - Reject Friction-Only Grasp Correction

**Date:** 2026-07-13

## Decision

`ACCEPT CONTACT-SPAN AND SWEEP EVIDENCE; REJECT FORCE CLOSURE AND GRASP SUCCESS`

Fresh same-agent review checked source/model binding, parameter isolation,
contact-point and normal provenance, two-body contact versus opposing contact,
metric simulation span versus physical aperture, implicit solver clamping,
training/holdout leakage, deterministic baseline, impact, assistance, teleport,
object clearance, friction-only overfitting, and authority escalation.

The metric contact-point profile is valid for this nominal MuJoCo attempt only.
Its collapse from 32.86691 mm to 4.907838 mm demonstrates that simultaneous
named-body contact does not establish force closure. No friction/compliance
training setting or held-out setting lifts the object. Friction-only tuning is
therefore rejected, and no candidate is promoted.

Only `mujoco_contact_span_profile_observed` and
`bounded_contact_property_sweep_observed` are accepted. Strict grasp, force
closure, physical aperture, physical twin qualification, simulation-training
readiness, optimizer work, and motion remain withheld. The strict evaluator's
future MuJoCo adapter must require opposing contact geometry rather than contact
count alone. The exact next experiment is a bounded wrist-pitch/object-yaw/
pregrasp lateral-offset search scored by opposing contact normals, contact span,
wrench closure, impact, unassisted lift, hold, lower, and release.
