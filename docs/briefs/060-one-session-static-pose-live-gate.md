# Slice Brief 060 - One-Session Static-Pose Live Gate

**Date:** 2026-07-12

## Objective

Open exactly one finite, read-only T16.5c candidate session after independently
verifying that the active parent thread uses the signed hardware-supervised
runtime. This transition is ineffective until its commit is confirmed on
`origin/codex/pi05-autolearn-loop`.

## Contract

- The continuation window runs from `2026-07-12T10:55:00-05:00` through
  `2026-07-12T13:55:00-05:00`; no new major slice begins after
  `2026-07-12T13:25:00-05:00`.
- The live gate runs only through `2026-07-12T11:25:00-05:00`, has session
  limit one and sessions-started zero, and uses scope
  `one_static_pose_bracket_candidate_session`.
- Before any device opens, reverify the current same-thread
  `danger-full-access`/`on-request` profile, obtain a fresh five-minute
  owner-presence lease, perform fresh metadata discovery, resolve the exact
  follower and both stable cameras, prove 640x480 RGB capture at integer 30
  FPS, and prove zero deduplicated holders across canonical and TTY aliases.
- Execute exactly `q_before -> two finite camera batches -> q_after ->
  no-torque close -> post-close all-alias holder check` with six
  `Present_Position` reads before and after and two frames from each camera.
- Forbid handshake, configuration/register writes, torque changes, motion,
  policy execution, training, overall-session retry, reconnect, and paid
  compute.
- Persist exactly one immutable private success or failure artifact after the
  session starts, clean up deterministically, and reclose the gate on every
  outcome.

## Evidence and authority

This transition grants only one candidate-session opportunity after remote
preservation. It grants no physical observation, reviewed policy input, model
load, inference, shadow, replay, actuation, qualification, or training label.
