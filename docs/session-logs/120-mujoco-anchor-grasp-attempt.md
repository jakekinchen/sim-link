# Session 120 - MuJoCo Anchor Grasp Attempt

**Date:** 2026-07-13

Brief 090 executed the declared 50 x 35 x 30 mm, 25 g nominal anchor cousin in
the pinned midpoint-calibrated SO-101 MuJoCo model. Image rendering was disabled
for this bounded dynamics audit, but every one of 371 non-image frames retains
joint state/action, object and gripper position, contact and support evidence,
contact-gated assist state, simulated actuator effort, contact force, and phase.
Two full runs match exactly.

The existing causal expert reacquired one gripper-side contact, then activated
its contact-gated weld. It lifted and placed the object, so the legacy tray
placement score reports pass. The strict ordered trace truthfully reports
analytic-expert controller ownership and weld assistance, not pure policy or
unassisted grasp success.

Strict evaluation rejects the trace for six reasons: peak 17.081659463 N
contact exceeds the 5 N threshold; physical actuator current has no calibrated
simulation mapping; gripper joint angle has no metric aperture profile; grasp
confirmation has one rather than two fingertip-side contacts; stable hold is
contact-invalid; and release still has one robot-object contact. The maximum
single-frame object displacement is 0.004194223 m, so no teleport is observed.

Artifact `32f14feb...` contains the complete selected raw evidence and compiled
trace. Nine focused tests and the 69-test relevant broad gate pass. No hardware,
physical motion, model inference, optimizer, training, Brev, paid compute, or
network was used.
