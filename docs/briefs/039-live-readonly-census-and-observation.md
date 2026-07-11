# Slice Brief 039 - Live Read-Only Census And Synchronized Observation

**Date:** 2026-07-11

## Objective

Execute T16.5b under the owner's bounded read-only authority. Reuse the remotely
verified T16.5a no-write lifecycle to resolve the desk-mounted SO-101 follower,
read the six expected STS3215 identities and declared telemetry, capture bounded
camera frames with host timestamps, and emit content-addressed evidence without
configuration, calibration, torque, register-write, goal, or motion operations.

## Entry and presence gate

- T16.5a implementation `f200087` and reviewer decision 047 must be ancestors of
  the confirmed `origin/codex/pi05-autolearn-loop` boundary `d002c80`.
- Immediately before the first live open, recheck local time against the
  12:14:07 CDT hard closeout and create a short session-scoped presence lease
  bound to owner authority `owner_supervised_physical_poc_2026_07_11`. The lease
  may not outlive the hard closeout and must identify the source owner message.
- If the owner-present lease cannot be truthfully revalidated, no live object is
  opened and work continues offline.
- Build and pass fake-backend, recorded-trace, static source, and cleanup tests
  for the exact live adapter and evidence writer before using the live path.

## Discovery boundary

- Discovery may inspect only operating-system USB, serial-device, and camera
  metadata. It must not open a serial port or camera during enumeration.
- Resolve one exact follower-role candidate from stable VID, PID, serial,
  canonical callout path, aliases, protocol, and baud evidence. A port path
  alone is insufficient.
- Reject zero or multiple follower candidates, a leader/follower alias collision,
  missing serial identity, path churn during the session, or any discrepancy
  between discovery and the pre-open contract.
- Do not instantiate `SOFollower`, a leader object, a robot aggregate, or any
  object whose connect path configures motors or cameras.

## Live servo boundary

- Construct only the reviewed raw Feetech bus behind
  `InjectedReadOnlyBusAdapter`, with IDs 1-6 and model `sts3215` bound to the
  pinned joint map.
- Connect only with `handshake=False`. Use only the T16.5a scalar read allowlist,
  `normalize=False`, and `num_retry=0`; the outer census owns the single bounded
  retry. Close exactly once with `disconnect(disable_torque=False)`.
- Read and verify model number, firmware major/minor, ID, baud, present position,
  voltage, and temperature for all six servos. Treat these as observations, not
  calibration or qualification.
- Record construct/connect/read/retry/close counts and keep register writes,
  torque changes, motion commands, and follower commands mechanically zero.
- Any unexpected method call, read shape, identity drift, retry exhaustion,
  telemetry loss, or cleanup failure ends the live attempt and closes through
  the no-write path.

## Camera and synchronization boundary

- Open only camera identities resolved by the pre-open discovery contract.
- Capture a finite small frame set, with wall-clock and monotonic host-receive
  timestamps, dimensions, encoding, frame byte hashes, and acquisition errors.
- Record servo observation intervals and camera receive intervals so the host-
  observed skew is computable. Do not claim hardware-clock synchronization when
  only host timestamps are available.
- Release each camera exactly once even on partial failure. No continuous
  recording, actuator command, policy call, or task execution is permitted.

## Evidence and privacy

- Write an immutable local-private evidence bundle containing exact raw device
  identities, operation trace, telemetry, and captured frames. Raw frames and
  hardware serial strings must not be pushed to the public remote.
- Write a separate tracked signed/content-addressed manifest using exact SHA-256
  fingerprints for redacted stable identities and local artifact bytes. It must
  preserve verification without exposing raw images or serial strings.
- The manifest may use only `live_read_only_census_observed` for the live census
  and `physical_observation_capture` for camera observations. It must explicitly
  set `physical_follower_commanded=false` and all write/torque/motion counts to
  zero.
- Fixture, local-private physical, tracked redacted physical, simulation, replay,
  and policy evidence remain distinct. This slice cannot emit physical
  qualification or autonomous-success claims.

## Adversarial acceptance

- Fake tests must reject ambiguous/missing USB identity, role and alias drift,
  path changes, wrong/missing/duplicate servo IDs, wrong models, malformed or
  non-finite values, unknown registers, extra/missing reads, double close,
  retry overflow, camera identity drift, frame failure, timestamp regression,
  hash mismatch, and cleanup that masks a primary exception.
- Static/source tests must prove the live module has no write, sync-write,
  enable/disable-torque, configure, calibrate, setup, scan, goal, or action call
  and that the only bus close passes `disable_torque=False`.
- A deliberate fake writable-backend attack must fail before any write-like
  method is invoked.
- Re-running manifest verification from unchanged local-private bytes must be
  deterministic; any identity, observation, count, timestamp, or frame change
  must alter the content identity.

## Validation

- Focused fake live-adapter/discovery/camera/evidence suite.
- Existing T16.5a, intervention, computed qualification, authority, twin,
  structural-twin, dependency-lock, and LeRobot regression gate.
- Offline dry-run and product verifier before live access.
- One bounded live discovery/census/camera attempt only after every entry gate.
- `py_compile`, formatting, static no-write inspection, and `git diff --check`.

## Stop conditions

Stop live work immediately on owner absence, identity or calibration ambiguity,
unexpected write-like activity, direction or model disagreement, telemetry loss,
threshold breach, unexpected contact, camera/path churn, cleanup failure, or
lease expiry. Close/release through the proven no-write paths and continue only
offline. Do not ask for broader motion authority.

## Authority after this slice

If reviewed and remotely preserved, this may establish only
`live_read_only_census_observed` and `physical_observation_capture` for the exact
session evidence. It grants no register write, torque change, motion, calibration,
physical qualification, policy actuation, training, transfer, promotion, or
global authority decision.
