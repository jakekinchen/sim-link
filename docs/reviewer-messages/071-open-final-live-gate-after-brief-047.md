# Reviewer Decision 071 - Open Final Live Gate After Brief 047

**Date:** 2026-07-11

## Decision

`OPEN T16.5B FOR EXACTLY ONE FINAL SIGNED-640X480 EXACT-DIMENSION SESSION`

Implementation `e68068a` and closeout `4b8d1d5` are remote. This gate is
ineffective until its transition commit is also confirmed on origin. It expires
at `2026-07-11T11:38:00-05:00`, allows one session, and requires a fresh
five-minute owner-presence lease.

The sequence is fresh discovery v2, both-alias zero holders, contract v3 with
each camera's own signed mode of at least 640x480, 54-read six-servo census with
all `Torque_Enable=0`, no-write close, both-alias zero holders, two exact-name
frames per camera, exact decoded dimensions, stable rediscovery, and v4 private
plus tracked evidence. Every mismatch rejects and recloses without retry.

No reconnect, Studio POST, signal, write, torque transition, motion, policy
actuation, qualification, optimizer, or paid compute is authorized. Sequential
capture remains not synchronized and not policy-shadow-input-valid.
