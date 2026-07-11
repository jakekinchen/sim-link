# Manager Intervention 014 - Resume On Owner-Authorized Virtual Disconnect

**Date:** 2026-07-11

## Decision

`RESUME T16.5b; EXECUTE ONE EXACT FOLLOWER DISCONNECT; KEEP LIVE GATE CLOSED`

## Evidence anchor

`100 - Owner resolved the exact human-authority boundary`

At `2026-07-11T08:53:51-05:00`, the fresh audit exactly reproduced the
pre-existing Studio follower holder and status: normalized holder identity
`642305133...`, hardware `79f4ce89...`, safety `8c425d38...`, routing
`620cb845...`, follower connected with torque reported on, route `none`, and
zero running jobs. The owner then stated that the arm cannot be unplugged and
authorized whatever virtual disconnect/reconnect work is possible.

The accepted immediate action is narrower than that broad wording: call
`POST /api/hardware/disconnect` exactly once with `{"role":"follower"}`. The
known route releases follower torque and closes only the follower serial bus.
Verify the response, GET-only hardware state, and reviewed zero-holder guard.
Do not signal the server, disconnect the leader, change safety/routing, issue a
motion command, or reopen the live gate in the same boundary.

Reconnect is permitted only if exact identity, calibration, and current-pose
evidence proves that enabling the connection cannot move from a stale goal.
Otherwise preserve the mechanically safer follower-disconnected/torque-off
state and continue T16.5b with a fresh read-only session after a separate
canonical live-gate reopen.
