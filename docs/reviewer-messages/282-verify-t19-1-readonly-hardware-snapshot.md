# Reviewer Decision 282 - Verify T19.1 Read-Only Hardware Snapshot

**Date:** 2026-07-16

## Decision

`ACCEPT T19.1 LIVE READ-ONLY HARDWARE SNAPSHOT; CLOSE AND CONSUME THE GATE`

Session `t19-1-20260716-0712-cdt` was authorized by fresh same-thread runtime
profile `0ab95c4e...`, central decision `2fd92308...`, and one-use permit
`93b229f4...` against remote gate boundary `80628ee`. The permit was active and
the private and tracked destinations were new before execution.

The exact follower resolved without camera enumeration. Both signed serial
aliases had zero holders before construction and after close. The pinned raw
Feetech bus connected once with `handshake=False`, completed exactly 54/54
allowlisted reads with zero retries, and closed once with
`disconnect(disable_torque=False)`. All six servos reported model 777,
firmware 3.9, and `Torque_Enable=0`. Observed voltage was 12.1-12.3 V and
temperature was 29-34 C. Register writes, torque changes, motion commands, and
unexpected operations were all zero; `physical_follower_commanded=false` and
`camera_accessed=false`.

Private snapshot `c0c877a0...` and tracked redacted manifest `f423f5d3...`
verify independently. The manifest binds request, decision, permit, runtime,
discovery, exact census contract, result `a7663498...`, both holder snapshots,
all six decoded servo records, and the zero-unsafe-operation counts without
containing the raw USB serial.

## Adversarial review

Fresh review rechecked authority linkage, permit activity and one-use output,
exact remote boundary, runtime/source binding, serial-role and alias identity,
pre/post holder closure, trace ordering and timestamps, exact register order,
retry count, decoded values, torque-enable state, no-torque close, private file
hash/size, manifest recomposition, non-finite values, serial redaction, and all
authority-withheld fields. The result is accepted only as
`t19_1_live_readonly_hardware_snapshot_observed`.

T19.2 remains a separate motion/calibration task. This decision grants no
camera use, write, torque change, motion, calibration, policy actuation,
physical-twin qualification, physical transfer, promotion, external compute,
or Brev authority.
