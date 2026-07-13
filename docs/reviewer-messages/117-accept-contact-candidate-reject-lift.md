# Reviewer Decision 117 - Accept Contact Candidate; Reject Lift

**Date:** 2026-07-13

## Decision

`ACCEPT LOW-IMPACT TWO-JAW CANDIDATE; REJECT UNASSISTED GRASP`

Fresh same-agent review checked finite-grid completeness, source identity,
single-frame two-jaw semantics, force ranking, wrist-roll and height isolation,
determinism, assistance state, object teleport, contact aggregation, normalized
gripper versus metric aperture, transient lift versus maintained clearance,
physical-source confusion, and authority escalation.

The selected -1.5 rad / 0.018 m candidate reproducibly establishes simultaneous
fixed- and moving-jaw contact below the strict impact limit. It does not retain
that grasp during lift: contact is lost and the object returns to the table.
The normalized joint range is not relabeled as fingertip aperture.

Only `low_impact_two_jaw_mujoco_contact_candidate_observed` is accepted.
Unassisted or strict grasp success, metric aperture, policy success, physical
twin qualification, simulation-training readiness, optimizer work, and motion
remain withheld. T16.5c remains in progress and T16.6 pending. The exact next
experiment is a geometry-derived nominal aperture map plus a bounded friction,
contact-compliance, and close-hold sweep at the accepted wrist-roll/pregrasp
pose, with an untouched held-out parameter setting and no weld assistance.
