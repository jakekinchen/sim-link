# Reviewer Decision 114 - Accept Midpoint Coordinate Correction; Reject Motion

**Date:** 2026-07-13

## Decision

`ACCEPT OFFLINE COORDINATE CORRECTION; REJECT MATCHED REPLAY AND MOTION`

Fresh same-agent adversarial review checked legacy-dataset mutation, implicit
limit projection, non-finite and wrong-width inputs, zero/sign ambiguity,
calibration-range substitution, uncalibrated visual overclaim, evidence-path
leakage, start-versus-prefix contact loss, replay nondeterminism, stale
content-addressed fixtures, and authority escalation.

The established v1 offset mapping is unchanged. A new separately versioned
midpoint-direct candidate rejects non-finite, wrong-width, and out-of-model
inputs by default; diagnostic projection requires an explicit opt-in. Its
source/range review selects direct identity for this session's offline replay
only. The accepted external frame supports articulated fold topology, not
metric camera alignment, so `physical_twin_qualified` remains false.

The corrected 5/10/15 replay is deterministic and finite. Measured `q_after`
maps without clamping, settles without robot self-contact, and every proposal
prefix has zero projection and zero robot self-contact. This proves Reviewer
113's clamping/contact result was a legacy-offset replay artifact. It does not
make the replay matched: the current physical workcell still differs from the
sorting simulator, no metric camera/workcell transform exists, policy-input
validity remains rejected, wrist roll is outside checkpoint support, and the
proposal reaches 5.43238 rad/s after a 54.4099-degree first wrist-roll change.

Only
`midpoint_direct_physical_pose_candidate_selected_for_offline_replay` and
`midpoint_coordinate_corrected_proposal_prefix_replay_diagnostic_observed` are
newly accepted. T16.5c remains in progress. Accepted shadow, matched replay,
`safe_enough_to_prepare_t16_6`, Stage A motion, twin qualification, simulation
training, optimizer work, Brev, and paid compute remain withheld. The next safe
experiment is the first executable Minimum Viable Grasping Twin slice around
the visible lightweight turquoise anchor.
