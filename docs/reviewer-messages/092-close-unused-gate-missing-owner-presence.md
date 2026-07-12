# Reviewer Decision 092 - Close Unused Gate On Missing Owner Presence

**Date:** 2026-07-12

## Decision

`STOP - CLOSE UNUSED LIVE GATE; WAIT FOR FRESH EXPLICIT OWNER PRESENCE`

Evidence anchor `100`: the owner-presence lease is a mandatory physical safety
boundary and cannot be inferred from an automatic goal continuation. After
three consecutive continuations without a fresh explicit response, Reviewer
091's gate is closed at `17:46:31` with sessions-started zero and before any
discovery or device access.

A future retry requires the owner to state they are currently physically at the
robot, followed by a new reviewed finite gate. No fixture work, weaker lease,
stale presence claim, or broad authority substitution is accepted. No physical,
model, replay, training, or T16.6 authority is granted.
