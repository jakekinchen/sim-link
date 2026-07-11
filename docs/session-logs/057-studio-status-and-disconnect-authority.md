# Session 057 - Studio Status And Disconnect Authority

**Date:** 2026-07-11

## Scope

Challenge the serial-holder blocker read-only and determine the exact effect of
the available graceful shutdown and hardware-disconnect paths.

## Read-only evidence

- The holder snapshot remained unchanged at one process and opened no serial
  device.
- Only documented GET endpoints were called: health, hardware status, safety,
  routing, and jobs.
- The server reports leader and follower connected, follower torque on, safety
  armed, no e-stop, follower route `none`, and zero running jobs.
- Redacted response hashes: hardware `79f4ce89...`, safety `8c425d38...`, routing
  `620cb845...`.

## Source audit

- SIGTERM unwinds `StudioServer.stop()`, which closes HTTP/WS/cameras but does
  not call hardware disconnect or torque release. Process exit would release the
  file descriptor while leaving the servo torque state unchanged.
- The follower hardware-disconnect route calls `release_torque()` and then
  `disconnect(disable_torque=False)`. It is a bounded safe-shutdown route but
  includes a motor-register torque-disable write.

## Authority state

Neither path was invoked. Manager intervention 012 escalates the exact choice to
the owner. The live gate and `training_lock` remain closed; no proof label,
motion, policy actuation, physical qualification, or training occurred.
