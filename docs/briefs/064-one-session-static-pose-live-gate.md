# Slice Brief 064 - One-Session Static-Pose Live Gate

**Date:** 2026-07-12

## Objective

Attempt to open exactly one finite T16.5c gate for one static-pose-bracket
candidate after formal same-thread profile verification and remote preservation
of this transition. Fail closed if the runtime changes before preservation.

## Contract

- Effective window: `2026-07-12T17:35:00-05:00` through
  `2026-07-12T18:05:00-05:00`.
- Session limit: one; sessions started at transition: zero.
- Required runtime: thread `019f5804-b684-7023-a599-4f803ac0aceb`, turn
  `73c2f16e-7024-445f-a3bc-a070289c4d14`, `danger-full-access`,
  `on-request`, profile identity `db93b63cd00c03de52910f8e4b7eeb16c03b1f5badf30211b92e59e226ca73fa`.
- The gate is ineffective until its scoped commit is confirmed on
  `origin/codex/pi05-autolearn-loop`.
- After remote confirmation, require a fresh short owner-presence lease, fresh
  USB/serial/camera discovery, exact follower and calibration identities,
  both signed serial aliases at zero holders, both stable camera identities and
  exact 640x480/30 modes, candidate-contract verification, and a new immutable
  private destination before device open.
- Execute at most one candidate session and reclose the gate on every outcome.

## Result

Rejected before effective open. The runtime changed to `workspace-write` at
`2026-07-12T17:34:16-05:00`, before the proposed opening time, remote
confirmation, lease, discovery, or device access. Sessions started remains zero.

## Authority withheld

The transition grants no device access by itself and never grants register or
configuration writes, torque changes, motion, handshake, retry, model load,
policy actuation, training, paid compute, or T16.6 authority.
