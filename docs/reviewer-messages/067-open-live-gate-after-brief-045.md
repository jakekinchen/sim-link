# Reviewer Decision 067 - Open Live Gate After Brief 045

**Date:** 2026-07-11

## Decision

`OPEN T16.5B LIVE GATE FOR EXACTLY ONE FRESH DISCOVERY-V2/CONTRACT-V3 SESSION`

## Evidence anchors

- Brief 045 implementation: `820a40f0339ccd1c5cfd71789bbea6cdf1b4f036`
- Canonical closeout: `a6da4b458895808b3bfb703319722f333350c63f`
- Disconnect proof:
  `627de4fd5715e281007ab5f19a37b0cb610b4d3b637b7b37933a41396ba3859b`
- All-alias holder snapshot:
  `b33a7cc062bc73c666031f6f5b36d5f0e142bea7f541d77a0754fe04ae1d689c`

## Gate

The gate is ineffective until this transition commit is pushed and confirmed
on `origin/codex/pi05-autolearn-loop`. It then permits exactly one new session,
expires at `2026-07-11T11:34:00-05:00`, and requires a newly issued five-minute
owner-presence lease plus a fresh signed contract v3.

The only allowed sequence is fresh discovery v2 with metadata-only signed
per-camera supported modes; zero holders across the signed canonical and paired
TTY paths; lease and contract creation; one read-only six-servo census;
no-write close; zero holders; two finite exact-name camera frames per pinned
camera; stable rediscovery; and private plus tracked v4 evidence finalization.
Each command must bind its camera's exact signed pixel format, dimensions, and
integer-30 framerate before input. All six `Torque_Enable` reads must be zero.

Any identity, mode, alias, holder, calibration hash, lease, telemetry, torque,
operation-count, camera, discovery-stability, cleanup, duration, privacy, or
evidence mismatch rejects the session, suppresses every success label/manifest,
and immediately recloses the gate. No retry session is implied. No reconnect,
Studio POST, process signal, configuration/register write, torque transition,
motion, policy actuation, physical qualification, optimizer, or paid compute is
authorized.

The transition itself performs no hardware discovery or open and grants no
proof label. Sequential census then camera evidence is finite physical capture
only; it is not synchronized or policy-shadow-input-valid.
