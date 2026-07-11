# Manager Intervention 012 - Studio Torque-On Owner Disconnect Decision

**Date:** 2026-07-11

## Decision

`ESCALATE TO OWNER; DO NOT SIGNAL SERVER OR CALL DISCONNECT`

## Evidence anchor

`100 - Proven safety and human-authority boundary`

## Evidence

- The reviewed holder check still returns one process and opens no device;
  snapshot SHA-256 is
  `642305133b602477840e31d756e52b11cf5d97e689eda15ae2741291ed47106c`.
- Documented GET-only Studio endpoints report both arms connected, follower
  torque on, safety armed, no follower route, and zero running jobs.
- Redacted status hashes are hardware `79f4ce89...`, safety `8c425d38...`, and
  routing `620cb845...`.
- `StudioServer.stop()` closes HTTP, WebSocket, and camera resources but does
  not call `HardwareManager.disconnect()` or release follower torque. SIGTERM
  would therefore release the process file descriptor without an explicit
  torque-off write.
- `/api/hardware/disconnect` calls `RealSO101Bridge.disconnect("follower")`,
  which calls `release_torque()` before no-torque bus close. That is the safer
  hardware shutdown route but includes a motor-register torque change.

## Owner choice

Choose exactly one:

1. Manually disconnect the follower in the existing Studio UI, then tell this
   Goal to recheck for zero holders.
2. Explicitly authorize one exact Studio follower-disconnect API call whose only
   motor write is torque release, followed by read-only zero-holder verification.
3. Keep Studio connected; T16.5b remains offline and no physical proof proceeds.

No SIGTERM, force kill, safety endpoint, disconnect endpoint, serial/camera open,
write, torque change, or motion is authorized while this choice is pending.
