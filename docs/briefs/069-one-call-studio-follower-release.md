# Slice Brief 069 - One-Call Studio Follower Release

**Date:** 2026-07-12

## Objective

Use the owner's fresh expanded authority to correct Reviewer 094's exact
blocker with one Studio follower-disconnect call, then verify torque off and
zero holders across both signed aliases.

## Permit

- Exactly one `POST http://127.0.0.1:8790/api/hardware/disconnect`.
- Exact JSON body: `{"role":"follower"}`.
- Authorized effect: release the Studio follower handle and its inherent
  follower torque-disable behavior.
- Required verification: HTTP response, read-only Studio status, and fresh
  all-alias deduplicated holder snapshot.
- No retry, reconnect, leader change, register/configuration write, motion,
  policy action, training, or paid compute.

The operation is ineffective until Reviewer 095 and this permit are remotely
preserved. Any non-2xx response or nonzero holder/torque-on result fails closed
and requires a new review.
