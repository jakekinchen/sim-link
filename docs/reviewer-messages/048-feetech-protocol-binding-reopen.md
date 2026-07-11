# Reviewer Decision 048 - Feetech Protocol Binding Reopen

**Date:** 2026-07-11

## Decision

`REOPEN T16.5a; KEEP T16.5b CLOSED; CORRECT PROTOCOL AND SOURCE BINDINGS OFFLINE`

## Finding

The pre-live pinned-source audit found that
`external/lerobot/src/lerobot/motors/feetech/feetech.py` declares
`DEFAULT_PROTOCOL_VERSION = 0` and the STS3215 model table also maps to protocol
`0`. The T16.5a fixture contract and result remotely preserved through
`d002c80` declared protocol `1`. A live `FeetechMotorsBus` constructed with that
value would reject STS3215 before opening, so the offline artifact is not a
truthful executable-runtime binding.

## Evidence

- Feetech implementation SHA-256:
  `0460413cd6a641cede015ac19ac53d2cfe9c343af1bd18ed74e1951229f64ff2`.
- Feetech tables SHA-256:
  `71f7f7beb17169781bd26a33b165ed4c5c3df7b9c477d36860f9d6011eb00428`.
- Runtime import reported default protocol `0`; source model table maps
  `sts3215` to `0`; constructor rejects incompatible protocol values.
- No hardware was enumerated or opened. The issue was found entirely from the
  pinned source before live-capable implementation.

## Authority consequence

Withdraw `census_trace_conformant`, return T16.5a to `in_progress`, and keep all
live serial/camera work closed until Brief 040 is implemented, reviewed, pushed,
and remote-confirmed. `training_lock` remains closed.
