# Minimal Live-Adapter Recreation Contract

**Status:** design-only T20.17 boundary; no live hardware was opened.

## Purpose

The current `live_readonly_observation.py` family is historical evidence and
must stay intact. A future recreation should not carry that implementation
forward. It needs a small adapter around pinned LeRobot camera/robot APIs that
proves a bounded read-only session, produces content-addressed evidence, and
fails closed everywhere else.

This is a replacement specification, not a claim that the future adapter has
been implemented, exercised, or permitted. It does not authorize device
enumeration, camera access, robot construction, serial access, or motion.

## Narrow interface

The adapter has three read-only operations and no action operation:

```text
issue_receipt = open_read_only_session(central_decision, owner_present_permit)
frame_receipt = retain_frame(issue_receipt, camera_observation)
close_receipt = close_session(issue_receipt)
```

`central_decision` comes only from the central authority composer. The adapter
does not infer a permit from a user name, device presence, prior evidence, or a
successful API call. `owner_present_permit` must name the exact read-only
scope, stack identity, expiry, owner-presence witness, and one session nonce.

No `move`, `send_action`, `set_motor`, `teleop`, `calibrate`, or generic
hardware-object escape hatch belongs in this surface. A later motion feature
would be a separate adapter, central decision, owner permit, and review
boundary.

## State machine

```text
absent
  -- valid central decision + owner-present read-only permit --> issued
issued
  -- matching pinned stack identity and unexpired nonce --> active
active
  -- one content-addressed camera observation --> active
active
  -- explicit close or expiry/error --> closed
issued/active/closed
  -- invalid signature, expiry, identity drift, duplicate nonce, or cleanup failure --> rejected
```

Only `active` may retain a frame. `rejected` is terminal and emits a signed
failure receipt without image bytes. `closed` cannot be reopened. Every state
transition is canonical-JSON signed with `artifact_contract.py`; the session
receipt carries the previous receipt identity so omitted or reordered events
cannot be silently stitched together.

## Required receipts

The data retained by a successful session is intentionally small:

| Receipt | Required content | Explicitly not a claim of |
| --- | --- | --- |
| Session issue | central decision identity, permit identity, nonce, wall-clock bounds, stack identity, camera role allowlist | camera access, robot access, motion authority |
| Frame | session identity, role, monotonic sequence, content SHA-256, pixel dimensions/format, capture-time bound, redaction classification | calibration, scene match, physical qualification |
| Session close | final sequence, frame receipt identities, cleanup result, expiry result | future session reuse |

Frame bytes are private by default. The signed manifest contains a content hash
and minimal safe metadata; it never substitutes a screenshot, thumbnail,
synthetic image, or a claimed digest for bytes that were not retained. A
redacted derivative is a new artifact with its own provenance, never a rewrite
of the source frame.

## Fail-closed rules

Reject the entire session if any of the following is missing, stale,
contradictory, or non-finite:

- central authority decision, owner-present permit, exact scope, nonce, expiry,
  or pinned LeRobot/adapter identity;
- one-to-one camera-role binding, sequence monotonicity, frame hash, or
  declared redaction classification;
- append-only predecessor receipt identity, cleanup proof, or error reason;
- evidence-mode label (`physical_read_only`, `synthetic`, `replay`, or
  `policy_evaluation`) consistent with the actual source.

Read-only capture is not a hardware lease, policy evaluation is not physical
proof, and an image hash is not a calibration result. The adapter may only add
a local capability such as `physical_read_only_frame_retained`; it cannot
grant `physical_twin_qualified`, `physical_transfer_ready`, or
`promotion_eligible`.

## Deletion boundary and migration

Keep the existing live-observation implementation and all historical signed
evidence unchanged until the new adapter has its own reviewed, source-bound
read-only proof. Recreate only the interface above using pinned LeRobot APIs;
do not port camera-trust-specific branches, serial discovery helpers, or
motion-adjacent code. Archive historical modules as evidence references rather
than treating them as runtime dependencies.

The same rule applies to data: a future episode source is created directly as
one `LeRobotDataset`, then bound by the signed native episode manifest and the
actual processor observation. It must not restore compiler-owned
frames/segments/windows storage or a preprocessing mirror merely to support
the adapter.

## Authority boundary

This document records a future design only. During its creation no camera,
robot, serial device, leader/follower, servo bus, or live hardware object was
accessed or instantiated; no external compute or Brev resource was used. A
future physical session remains subject to the formal runtime verifier, new
owner authority, a fresh permit, and a separately reviewed execution boundary.
