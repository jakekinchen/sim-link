# Reviewer Decision 086 - Open One Static-Pose Live Gate

**Date:** 2026-07-12

## Decision

`CONTINUE T16.5C; OPEN EXACTLY ONE READ-ONLY STATIC-POSE CANDIDATE SESSION AFTER REMOTE CONFIRMATION`

The active parent thread is independently verified as
`danger-full-access`/`on-request` with the permissions profile disabled. Brief
059 and its reviewed implementation `f6b6c08299ddc9a460e6ec5c711fd0783cd2356a`
are on origin. The new finite continuation and live-gate windows are explicit.

This transition permits one fresh session only after its own commit is present
on `origin/codex/pi05-autolearn-loop`. Before device open it requires a fresh
hardware-profile capture, five-minute owner-presence lease, discovery, exact
follower/calibration/camera identity and 640x480-at-30-mode verification, and
zero holders across both serial aliases.

The sole allowed session is six `Present_Position` reads, two frames from each
signed camera, six more `Present_Position` reads, no-torque close, and a
post-close all-alias holder check. It must write exactly one immutable private
success or failure artifact and reclose the gate on every outcome. No handshake,
write, torque change, motion, policy execution, retry, reconnect, training, or
paid compute is authorized.

Evidence anchor `100`: opening any device before remote confirmation, profile
reverification, lease, discovery, or zero-holder proof is prohibited. This
decision grants no observation acceptance, reviewed policy input, model load,
inference, shadow, replay, actuation, qualification, or training authority.

The same-agent review found no write, torque, motion, policy, training, retry,
or authority-escalation path in the transition. Thirty-four focused tests pass
in each pinned runtime, both exact source verifiers and the canonical gate-state
audit pass, and the 374-test broad offline authority/twin regression is green.
