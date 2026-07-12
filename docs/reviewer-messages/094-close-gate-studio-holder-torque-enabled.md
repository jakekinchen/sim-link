# Reviewer Decision 094 - Close Gate On Studio Holder And Torque Enabled

**Date:** 2026-07-12

## Decision

`STOP - CLOSE LIVE GATE; FOLLOWER RELEASE AND TORQUE-OFF REQUIRED`

Evidence anchor `100`: the exact follower has one independent Studio holder and
the Studio read-only status reports torque enabled. Both contradict mandatory
pre-open conditions. The candidate session did not start; sessions-started is
zero; no private session artifact or device open exists.

The consumed one-call disconnect permit cannot be reused or bypassed by killing
the Studio process. The owner must release the follower in Studio or explicitly
grant a new, separately scoped disconnect operation. A new reviewed gate,
fresh lease/discovery, torque-off check, and zero-holder evidence are required
after correction. No shadow, replay, motion, training, or T16.6 authority is
granted.
