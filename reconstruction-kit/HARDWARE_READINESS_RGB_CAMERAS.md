# RGB Camera Hardware Readiness — 2026-07-16 Census

## Verdict

**Not ready from this session.** The owner-present RGB-only census was attempted
once under central decision `7990e413...` and one-use permit `6341a190...`.
That permit is consumed. No signed camera frame or trustworthy current stream-
configuration list was accepted, so this note must not be read as camera
qualification.

## What happened

- The exact D405 UVC RGB source was the first target. It opened through named
  AVFoundation, returned one decoded PNG, and was released.
- The decoded PNG dimensions differed from the signed selected input mode. The
  fail-closed validator rejected the frame before signing or retention.
- The sequential session stopped at that first failure. The C922 was not
  opened, so no C922 frame or current mode census was accepted.
- The first implementation did not persist signed discovery metadata before
  opening the source. Therefore its advertised-mode list is unavailable after
  rejection and is deliberately not reconstructed from memory.
- No coarse latency result is reported because there is no accepted signed
  frame boundary to carry it.

Tracked terminal receipt:
[`rgb_camera_census_failure_20260716_2242.json`](../configurations/robot_lab/rgb_camera_census_failure_20260716_2242.json)
(`5c0edf59...`). The private failure file remains outside the portable kit and
is bound by hash/size in that receipt.

## Safety boundary

Depth/librealsense, serial enumeration/open, register reads/writes, torque,
motion, audio, inference, training, and physical-follower commands were all
zero. The camera subprocess was closed; no live ffmpeg capture remained after
the rejection. This is a safe terminal infrastructure failure, not a camera
readiness pass.

## Exact replacement requirement

A future owner-authorized session should first persist the signed D405/C922
discovery and advertised formats before any open. Its failure evidence must
retain requested input width/height, decoded PNG width/height, pixel format,
camera role, and capture audit. Only then should a separately reviewed adapter
distinguish requested input raster from decoded output raster (including any
deterministic orientation transform) and retry one frame per camera. No
additional camera session is authorized by this note.
