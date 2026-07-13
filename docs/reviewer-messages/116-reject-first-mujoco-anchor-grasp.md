# Reviewer Decision 116 - Reject First MuJoCo Anchor Grasp

**Date:** 2026-07-13

## Decision

`ACCEPT DETERMINISTIC ATTEMPT EVIDENCE; REJECT STRICT GRASP SUCCESS`

Fresh same-agent review checked pinned-model and nominal-object identity,
physical-versus-simulation source confusion, two-pass determinism, raw-frame
retention, phase ordering, contact-force and support derivation, robot
self-contact, teleport, controller-assist disclosure, current and aperture
fabrication, contact counting, release state, legacy score conflation,
actor-privilege leakage, and authority escalation.

The 371-frame attempt is deterministic and the legacy final placement score is
true. That score depends on a contact-gated weld after only one gripper-side
contact and is not a strict grasp. The strict evaluator correctly rejects peak
impact, missing current/aperture calibration, missing two-sided contact, invalid
stable hold, and contact-retaining release. No thresholds or missing values were
weakened or invented.

Only `deterministic_mujoco_anchor_grasp_attempt_observed` is accepted. Unassisted
MuJoCo grasp success, strict policy success, physical anchor profiling, twin
qualification, simulation-training readiness, optimizer work, and physical
motion remain withheld. T16.5c remains in progress and T16.6 remains pending.
The exact next experiment is a lower-force object-relative pregrasp/close that
requires simultaneous fixed- and moving-jaw contact, followed by a stable hold
and clean release, while deriving a nominal simulation-only aperture profile
from the pinned gripper kinematics.
