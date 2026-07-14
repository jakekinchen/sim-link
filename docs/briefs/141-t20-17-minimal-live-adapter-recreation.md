# Slice Brief 141 - T20.17 Minimal Live-Adapter Recreation

**Date:** 2026-07-14

## Objective

Write the compact invariant contract for recreating the large historical
physical-twin/live-observation stack as a future adapter over LeRobot camera
and robot APIs. This is design-only: the current stack and its evidence remain
immutable.

## Contract

- Express owner-present permits, read-only sessions, content-addressed frames,
  exact device/stack identity, expiry, and fail-closed session cleanup as
  independent small rules.
- Specify an adapter with no action API. A separate central authority decision
  and a distinct owner permit would be prerequisites for any later motion path.
- Separate captured physical bytes, redacted metadata, synthetic fixtures, and
  policy-evaluation evidence. No category promotes another.
- Show how the new adapter uses the existing artifact contract and central
  authority composer without reproducing camera-trust litigation logic.

## Acceptance Criteria

- The recreation document names the minimal state machine, input/output
  receipts, invalidation cases, and deletion boundary.
- It states explicitly that this task did not import, enumerate, open, or
  instantiate a camera, robot, serial device, or live hardware object.
- It preserves the distinction between a future design, a read-only proof, and
  physical/transfer/promotion authority.

## Out Of Scope

Any device discovery, camera capture, robot construction, serial access,
motion, hardware tests, live-stack deletion, external compute, or Brev.
