# Reviewer Decision 051 - Live Read-Only Metadata Discovery Reviewed

**Date:** 2026-07-11

## Decision

`ACCEPT METADATA COMPATIBILITY CORRECTION AND DISCOVERY; AUTHORIZE EXACT LEASE/CONTRACT AFTER REMOTE PRESERVATION`

## Review targets

- Compatibility correction commit
  `b85a2532de0913d54a9b73f71ae4e5d92b665632`.
- Private metadata discovery identity
  `53440393505ef25a27fc84cb1c736a49e9c8456f3b9ffff56140e03304d7b6e3`.

## Findings

- The operating system omitted only the descriptive USB manufacturer label.
  Stable VID, PID, serial, pinned callout path, product, location, HWID, role
  separation, protocol, and baud evidence were present and signed.
- Brief 039 does not make a descriptive manufacturer label an authority field.
  The correction therefore removes only that overconstraint while preserving
  every stable identity prerequisite and the exact discovery hash.
- The saved discovery resolves exactly one follower-role device and rejects the
  leader role by path/alias and serial identity. The redacted follower identity
  hash is `321be886b3a9599b7181c21df242d2dc7259bb05908c7ccc058d2058dbc640ca`.
- Both enumerated camera indexes map one-to-one to stable system camera
  identities. Their ordered redacted set hash is
  `427eaa2903590d64b39bb65fe2a4683623ec675b2faa9479f56e1cdc25338197`.
- The pinned follower calibration file has six exact expected joint keys and
  SHA-256 `192404b6d3c1337495d69649969459aa9d3f66816cd916c67da2588815e93ec4`.
- Discovery recorded four serial candidates, two selected cameras, zero serial
  ports opened, and zero cameras opened. It contains no servo response,
  telemetry, or frame and establishes no live proof label.

## Evidence

- 14 dedicated live-harness tests passed after correction.
- 30 combined live-harness and T16.5a census tests passed.
- 209 feeding/consuming regression tests passed in 71.076 seconds.
- The actual signed discovery revalidated through the corrected follower
  resolver and exact two-camera selector without any additional enumeration.
- Cached Black, `py_compile`, static safety tests, and `git diff --check` passed.

## Adversarial review

The correction was reviewed as a four-line authority change, not as a general
relaxation. Manufacturer remains present as `null` in the signed discovery and
is still bound into the downstream execution contract; it is simply not a
stable role-selection or returned target-identity prerequisite. A new test
proves the optional-label case yields the identical stable follower identity;
missing serial, ambiguity, leader collision, path drift, and signed metadata
changes remain rejected. No hardware-open path changed.

## Authority

After the correction and this reviewer record are remotely preserved, the
saved exact discovery may be used to create a short session-scoped
owner-presence lease and signed execution contract. A single bounded live
read-only attempt is permitted only if that contract, current time, remote tip,
source pins, calibration hash, follower identity, camera selection, and
pre-open discovery stability all validate. This decision grants no write,
torque change, motion, physical qualification, training, transfer, promotion,
or global authority. It establishes neither `live_read_only_census_observed`
nor `physical_observation_capture`; `training_lock` remains closed.
