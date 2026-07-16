# Session 286 - T19.1 Read-Only Hardware Snapshot

**Date:** 2026-07-16

Reviewer 281's gate transition was remotely confirmed at `80628ee`. Fresh
formal runtime capture proved this exact thread at the exact checkout uses
`danger-full-access` with approval policy `never`. Central composition granted
decision `2fd92308...` and one-use permit `93b229f4...`, expiring at 07:14:34
CDT; no hardware was accessed during preflight.

The permitted session completed in 3.6 seconds. Serial-only discovery resolved
the expected follower; both aliases were holder-free before and after. The
six-servo census performed exactly 54 successful reads, zero retries, one
connect, and one no-torque close. All servos reported model 777, firmware 3.9,
and torque disabled. There were zero register writes, torque changes, motion
commands, unexpected operations, follower commands, or camera accesses.

Private evidence remains under
`outputs/robot_lab/t19_1/private/t19-1-20260716-0712-cdt/`. Tracked manifest
`configurations/robot_lab/t19_1_readonly_hardware_snapshot_20260716_0712.json`
has identity `f423f5d3...` and excludes the raw hardware serial. Reviewer 282
accepts T19.1 and closes the consumed gate. No Brev or paid compute was used.
