# Reviewer Decision 052 - Rejected Live Attempt Camera Identity Redirect

**Date:** 2026-07-11

## Decision

`REJECT T16.5B LIVE ATTEMPT 001; CLOSE LIVE GATE; CONTINUE OFFLINE UNDER BRIEF 041`

## Review target

The single bounded execution of contract
`2102227cedc18e0b21152863424817781eff9bba139c986c8496e898bf2c22e9`
under remote boundary `e351f697f4f91494bf5a171309ff7a7cfc0ec284`.

## Findings

- The command reached post-close discovery, which is sequenced only after the
  no-write census returned closed and both finite camera objects returned from
  release cleanup.
- Post-close discovery rejected the attempt because the same two AVFoundation
  camera names exchanged numeric indexes. A later metadata-only snapshot
  confirmed that the camera-name set and system-camera record set were stable
  while order/index association changed.
- Because capture used numeric indexes, the recorded frames cannot be bound to
  their intended stable camera identities. The entire attempt is rejected.
- The failure occurred before private bundle or tracked manifest writing. No
  partial bundle or manifest exists and no success proof label was emitted.
- A read-only process inspection found a pre-existing July 8 `studio_server`
  process holding the follower serial device. It predates this Goal and was
  preserved untouched. Exclusive bus ownership is therefore unproven.
- The attempt exposed no write, torque, configuration, calibration, motion, or
  policy-actuation call. `physical_follower_commanded` remains false, but this
  safety fact does not convert the rejected attempt into accepted evidence.

## Review correction

Brief 041 requires a stable name/unique-ID-bound finite camera subprocess,
order/index-insensitive stable discovery comparison, exact PNG framing,
watchdogs, cleanup, and adversarial fake coverage. It also keeps all live access
closed while the independent serial holder remains unresolved.

## Authority

No T16.5b live proof label is granted. T16.5c and T16.6 remain closed. Further
offline implementation under Brief 041 is authorized; further serial or camera
open is not. Stopping or altering the pre-existing Studio server requires owner
direction. No write, torque change, motion, physical qualification, training,
transfer, promotion, or global authority is granted. `training_lock` remains
closed.
