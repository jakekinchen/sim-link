# Session 060 - Virtual Follower Disconnect And Zero-Holder Proof

**Date:** 2026-07-11

## Operation

At `2026-07-11T08:57:17-05:00`, after the owner-authority boundary was
confirmed on the named remote at `59f09d1`, the executor called exactly once:

```text
POST http://127.0.0.1:8790/api/hardware/disconnect
{"role":"follower"}
```

The call returned HTTP 200 with `{"connected":false}`. It was not retried. No
process signal, leader endpoint, safety endpoint, routing endpoint, motion
command, policy command, serial/camera capture, or training operation ran.

## Verified postconditions

- hardware state `d58a7549bfb030a2036c9b45cbc7e4c383d235c8e1bf8da718561f9f85267e83`:
  follower disconnected, follower torque false, leader still connected;
- follower holder snapshot
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`:
  exactly `[]`, count zero;
- safety state unchanged at `8c425d38bd0ba65416df488252d8642168cc49bddf5b6fe31a516caa782da655`;
- routing state unchanged at `620cb845cb8f1507263fdf7b6aec651a69e4b028d90628c935b0af0b533fdcb4`;
- zero running jobs;
- `physical_follower_commanded=false` and motion-command count zero.

The only write was the owner-authorized torque-disable inherent in follower
disconnect. The follower remains disconnected and torque off. The live gate is
still closed until this boundary is committed, pushed, and separately reopened.

## Persisted Goal control

At `2026-07-11T08:59:34-05:00`, the owner explicitly authorized every Goal-
control action needed to resume the existing workflow. `get_goal` still returned
the historical `blocked` status, and a replacement `create_goal` call was
rejected because the service considers that Goal unfinished. The runtime exposes
no resume transition, so the executor did not falsely mark the unfinished Goal
complete. The owner messages are recorded as the resumed run, the blocked audit
is reset, and work continues under the unchanged repository authority bounds.
