# Slice Brief 212 - T19.1 Owner-Present Read-Only Hardware Census

**Date:** 2026-07-16

## Objective

Complete T19.1 with one fresh, immutable snapshot of the desk-mounted SO-101
follower's six STS3215 servos. Read identity, firmware, baud, position, voltage,
temperature, and torque-enable registers through the already-reviewed narrow
transport. Perform zero register writes, zero torque changes, zero motion, and
no camera access.

## Authority and entry gates

- Owner presence and read-only hardware access are valid only through
  `2026-07-16T10:05:00-05:00`; the current run hard-closeout is earlier and
  therefore controls.
- Before any device enumeration or open, the exact current Codex thread must
  pass the formal `danger-full-access` plus approval-policy `never` verifier.
- Extend the T16.2b-A central composer with a narrowly scoped physical
  read-only-session decision. It must derive its decision from the canonical
  task state, current owner window, remotely confirmed gate boundary, formal
  runtime evidence, and finite timestamps. Callers cannot supply a granting
  boolean.
- A signed, content-addressed, one-use session permit must bind the exact
  branch, remote boundary, session ID, runtime-profile identity, central
  decision identity, 54-read plan, zero-write/no-motion invariants, and private
  immutable destination. The permit expires no later than five minutes after
  issuance or the run hard-closeout, whichever comes first.
- The implementation, tests, this brief, and the open-gate state transition
  must be reviewed, committed, pushed, and confirmed on
  `origin/codex/pi05-autolearn-loop` before the permit can grant.

## Exact live sequence

1. Reverify the active runtime profile, central decision, permit, branch,
   remote boundary, time window, source bindings, and one-use state.
2. Enumerate serial metadata only. Resolve exactly one pinned follower identity
   across canonical callout and TTY aliases; reject ambiguity or drift.
3. Prove zero holders across both aliases before construction.
4. Construct only the pinned raw Feetech bus, connect with
   `handshake=False`, and perform the exact six-servo allowlisted 54-read plan
   with `normalize=False` and inner retry zero.
5. Close exactly once with `disconnect(disable_torque=False)` and prove both
   aliases have zero holders afterward.
6. Emit private exact evidence and a tracked redacted manifest. Reclose the
   gate and consume the permit on success or failure.

No camera, leader, robot aggregate, `SOFollower`, Studio POST, reconnect,
configuration, calibration, scan, write, torque transition, goal, action,
policy, optimizer, Brev, paid compute, or destructive path is permitted.

## Tests and adversarial review

- Add deterministic tests before the live path for denied state, expired owner
  window, stale/wrong-thread runtime, unconfirmed remote boundary, forged
  decision or permit, reuse, path escape, source drift, serial ambiguity,
  holder presence, unexpected register/method, write-like activity, nonzero
  torque enable, malformed/non-finite results, cleanup failure, and evidence
  tampering.
- Run the focused T19.1, authority-composer, runtime-profile, T16.5a census,
  and live-readonly suites plus the relevant broad robot-lab gate.
- Perform a fresh same-agent adversarial review before the open-gate commit and
  again over the complete result boundary.

## Proof boundary

A successful reviewed result may grant only
`t19_1_live_readonly_hardware_snapshot_observed`. It does not calibrate the
twin, grant motion/contact authority, prove physical transfer, accept a policy,
or change promotion authority. T19.2 remains separately gated.
