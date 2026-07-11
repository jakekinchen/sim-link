# Reviewer Decision 061 - Open Live Gate After Brief 043

**Date:** 2026-07-11

## Decision

`OPEN T16.5B LIVE GATE FOR AT MOST ONE FRESH FINITE SESSION`

## Evidence anchors

- Implementation: `7ea26651e921eee55dad6fcbb26cb58c45c7b290`
- Canonical closeout: `37108426ba71a0625a32b29a1aa902bf7439f1ab`
- Disconnect proof:
  `627de4fd5715e281007ab5f19a37b0cb610b4d3b637b7b37933a41396ba3859b`
- All-alias holder snapshot:
  `b33a7cc062bc73c666031f6f5b36d5f0e142bea7f541d77a0754fe04ae1d689c`

## Gate

The live gate may become effective only after this transition commit is pushed
and independently observed on `origin/codex/pi05-autolearn-loop`. It permits one
new session, expires at `2026-07-11T10:43:00-05:00`, and requires a newly issued
five-minute owner-presence lease and exact execution contract.

The only allowed sequence is fresh metadata discovery, zero holders across the
signed canonical and paired TTY paths, lease and contract creation, one
read-only six-servo census, no-write close, zero holders, finite exact-name
camera batches, and stable discovery/evidence finalization. All six
`Torque_Enable` values must be zero. Every raw read must match the contract and
decoded trace; teardown must use `disable_torque=false`.

Any identity, alias, holder, calibration hash, lease, telemetry, torque,
operation-count, camera, discovery-stability, cleanup, duration, privacy, or
evidence mismatch rejects the session and immediately recloses the gate. No
retry session is implied. No reconnect, signal, Studio POST, configuration or
register write, torque transition, motion, policy actuation, physical
qualification, or training is authorized.

The transition itself performs no hardware enumeration or open and grants no
proof label. Sequential census then camera evidence may be labeled finite
physical capture only; it is not synchronized or policy-shadow-input-valid.

Post-transition validation confirmed the disconnect-proof maintenance command
fails closed while `live_gate=open`; it did not mutate either proof artifact.
