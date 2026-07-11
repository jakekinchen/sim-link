# Reviewer Decision 050 - Live Read-Only Observation Harness Reviewed

**Date:** 2026-07-11

## Decision

`ACCEPT T16.5B OFFLINE HARNESS; AUTHORIZE METADATA DISCOVERY ONLY AFTER REMOTE PRESERVATION`

## Review target

Implementation commit `16d24ea0c4ced2b62d3ba2c0297f1816981efee3`
under corrected Brief 039.

## Findings

- The CLI separates offline verification, metadata-only discovery, private
  lease/contract preparation, and the one bounded capture operation. Offline
  verification imports no discovery or live-object path.
- The live contract binds the corrected protocol-0 T16.5a source semantics,
  exact follower USB role, leader aliases, calibration-file identity, session,
  owner authority, short presence lease, selected camera identities, duration,
  retry policy, and allowed/forbidden operations.
- Discovery uses operating-system serial/USB and camera metadata only and
  records zero opened ports and cameras. Missing, ambiguous, colliding, or
  drifting identities fail closed.
- The raw Feetech bus is hidden behind a narrow adapter. Its only available
  lifecycle is `connect(handshake=False)`, scalar allowlisted reads with
  `normalize=False` and `num_retry=0`, and exactly one
  `disconnect(disable_torque=False)` cleanup attempt. No SOFollower or robot
  aggregate is instantiated.
- The outer census owns at most one transient retry, verifies IDs 1-6, STS3215
  model number 777, firmware, baud, raw position, voltage, and temperature, and
  requires zero register writes, torque changes, motion commands, unexpected
  operations, and follower commands.
- Camera capture is finite, timestamped on the host, content-hashed, and
  released on success or failure. Primary and cleanup failures remain visible
  together.
- Exact raw identities, telemetry, trace, and frames stay in a new immutable
  local-private directory. The tracked manifest carries hashes, counts,
  redacted stable identities, host timing, and the exact permitted proof labels
  without raw serial strings, device paths, camera identities, or frame bytes.
- No live proof label is established by this review because no device metadata
  has been enumerated and no serial port or camera has been opened.

## Evidence

- 14 dedicated live-harness tests passed.
- 30 combined live-harness and T16.5a census tests passed.
- 209 feeding/consuming regression tests passed in 71.561 seconds.
- The offline verifier exited zero under both `.mujoco_venv` and the exact
  `external/leLab/.venv` intended for discovery/capture. Both reported protocol
  0, the four corrected source hashes, `hardware_enumerated=false`, and
  `hardware_opened=false`.
- Black, `py_compile`, static forbidden-call/source inspection, and
  `git diff --check` passed.

## Adversarial review

The fresh committed-diff review checked authority escalation, stale ancestry,
identity aliasing, source import drift, retry overflow, partial connect cleanup,
double close, unknown registers, re-signed evidence tampering, camera identity
ambiguity, timestamp regression, frame-hash drift, partial bundle writes,
privacy leakage, and primary/cleanup exception masking. The stale pre-correction
T16.5a ancestry in Brief 039 was replaced with corrected commits
`5102422`/`eeb16e1`, reviewer 049, and remote boundary `2407299`. No
implementation correction was required.

## Authority

After this reviewer record and implementation are remotely preserved on the
named branch, the next permitted operation is metadata-only discovery. This
decision does not itself authorize a serial or camera open and establishes
neither `live_read_only_census_observed` nor `physical_observation_capture`.
Opening devices still requires an exact discovery result, current owner-presence
lease, unexpired signed execution contract, stable identities, and all runtime
checks. It grants no write, torque change, motion, physical qualification,
training, transfer, promotion, or global authority. `training_lock` remains
closed.
