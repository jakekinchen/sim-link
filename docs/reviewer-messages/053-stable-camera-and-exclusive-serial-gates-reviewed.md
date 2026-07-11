# Reviewer Decision 053 - Stable Camera And Exclusive Serial Gates Reviewed

**Date:** 2026-07-11

## Decision

`ACCEPT BRIEF 041 OFFLINE CORRECTION AFTER REMOTE PRESERVATION; KEEP LIVE GATE CLOSED`

## Review targets

- `ea99ec9d371ad5a5f91c37aa9bd89d494ec41f43` - stable named-camera capture.
- `66003d899663ec91bf8ec7b23bc5e92388c87f55` - PNG pixel-stream validation.
- `fd13bf6e58359e5a5f3b61e25a00424050b599fa` - end-to-end audit evidence.
- `01802a0fd6a93eee658dbd945830a47acf916913` - exclusive serial-holder gates.

## Findings

- Canonical `live_gate: closed` now mechanically blocks presence-lease creation,
  so documentation drift cannot reopen hardware.
- Camera selection binds one exact AVFoundation name to one exact
  `system_profiler` unique ID/model. Duplicate names or IDs and stable identity
  drift fail closed; numeric index/order churn is explicitly non-authoritative.
- Production capture no longer imports OpenCV or calls `VideoCapture`. It starts
  ffmpeg with `shell=False` and the exact camera name, requests exactly two
  RGB24 PNG frames, and applies the five-second finite batch watchdog.
- PNG evidence validates signatures, bounded chunks, CRCs, one RGB8 IHDR,
  zlib-compressed pixels, exact scanline size/filter bytes, exact frame count,
  and zero trailing bytes. Nonzero exit or stderr rejects the batch.
- Success evidence records subprocess start/communicate/wait, frame delivery,
  release, terminate, kill, property-write, and continuous-recording counts.
  Private evidence retains exact identities; the tracked manifest retains only
  audit hashes, counts, timestamps, dimensions, and frame hashes.
- The capture CLI now parses normalized `lsof` holder records immediately before
  serial open and immediately after no-write close. Any holder, malformed
  output, or command failure rejects the attempt; accepted evidence requires
  zero holders in both snapshots. The guard never stops or signals a process.
- The pinned Feetech SDK remains locked to `feetech-servo-sdk==1.0.0` with the
  checked-in sdist hash. Its installed handler opens at the declared baud,
  clears only the host input buffer, and closes without a motor-register write.
- Rejected attempt 001 remains immutable rejected history. No later fake or
  offline correction supplies its missing live evidence.

## Evidence

- 19 dedicated live-harness tests passed.
- 35 combined live-harness and T16.5a census tests passed.
- 214 feeding/consuming regression tests passed in 71.210 seconds.
- End-to-end fake named-camera capture proved subprocess counts and per-camera
  audit hashes survive private evidence and the privacy-redacted manifest.
- Both supported runtime offline verifiers reported protocol 0, four pinned
  LeRobot source hashes, `hardware_enumerated=false`, and
  `hardware_opened=false`.
- Black, `py_compile`, static no-write/no-aggregate/no-OpenCV inspection, and
  `git diff --check` passed.

## Adversarial review

The complete four-commit diff was checked for shell/name injection, duplicate
camera identities, index churn, malformed/truncated/extra/CRC-valid but
zlib-invalid PNGs, non-finite or oversized dimensions, timeout, nonzero exit,
stderr, terminate/kill/wait accounting, cleanup exception masking, holder
record spoofing, concurrent serial ownership, privacy leakage, proof relabeling,
and live-gate bypass. Review-time corrections added pixel decompression/scanline
validation, end-to-end evidence propagation, and the zero-holder serial gate.

## Authority

After remote preservation, Brief 041 grants only
`stable_named_camera_capture_offline_verified` and
`exclusive_serial_holder_gate_offline_verified`. The live gate remains closed
because exclusive ownership has not been re-established after one pre-existing
Studio server was observed holding the follower device. This decision
does not authorize stopping that process or opening a serial port/camera and
grants no live proof label, write, torque change, motion, physical
qualification, policy actuation, training, transfer, promotion, or global
authority. `training_lock` remains closed.
