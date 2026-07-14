# Session Log 174 - T20.17 Minimal Live-Adapter Recreation

## Scope

Implementation `61f2d8c4216adba0453fb1b9e065a83b24c97392` records the compact
future contract in `minimal-live-adapter-recreation.md`. It replaces neither
the current historical live-observation code nor any signed physical evidence.

The design has only `open_read_only_session`, `retain_frame`, and
`close_session`. It binds a central authority decision and owner-present permit
to an expiring one-time nonce, pinned stack identity, append-only signed
receipt chain, and content-addressed private frame bytes. It has no action or
hardware-object API.

## Validation

- The contract names its complete state machine, successful receipts, terminal
  invalidation cases, evidence-mode separation, and historical deletion
  boundary.
- Brief 141 and the recreation map agree that this is a future adapter over
  pinned LeRobot APIs, not a rewrite of the present stack.
- JSON parsing, pointer synchronization, and diff checks passed. This was a
  design/documentation slice; no hardware or package runtime was invoked.

## Authority

No camera, robot, serial device, leader/follower, servo bus, or live hardware
object was accessed or instantiated. No motion, model, optimizer, external
compute, or Brev action occurred. The document grants no read, motion,
physical-transfer, or promotion authority.
