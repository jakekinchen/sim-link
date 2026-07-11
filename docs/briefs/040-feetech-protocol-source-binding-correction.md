# Slice Brief 040 - Feetech Protocol Source-Binding Correction

**Date:** 2026-07-11

## Objective

Correct and reverify T16.5a before any live access. The pinned LeRobot STS3215
runtime uses Feetech protocol version `0`, while the offline census fixture
incorrectly declared `1`. Replace that value, mechanically bind every bus/model/
joint constant used by the census to exact pinned source files, regenerate the
signed artifacts, and rerun the complete review and remote-preservation gate.

## Required correction

- Set the STS3215 census protocol to `0`; keep baud 1,000,000, model number 777,
  resolution 4096, IDs 1-6, and the exact follower joint map.
- Add code-pinned content hashes for the exact Feetech implementation, Feetech
  table, generic motor-bus lifecycle, and SOFollower joint-map source files.
- Add an independent source-binding verifier that parses the pinned source and
  proves protocol default/model protocol, baud default/code, model number,
  resolution, register widths, connect/disconnect defaults, and six joint
  IDs/models. Do not trust duplicated serialized constants alone.
- Make checked-in artifact verification fail closed on a changed source hash or
  semantic source value.
- Add an explicit regression showing protocol `1` is rejected and cannot reach
  a live constructor.

## Validation

- Focused census/source-binding tests and deterministic artifact regeneration.
- Full intervention, qualification, authority, twin, dependency, and LeRobot
  feeding/consuming regression gate.
- All relevant product verifiers, `py_compile`, formatting, static no-live-
  factory/no-write inspection, and `git diff --check`.
- Fresh same-agent adversarial review and remote confirmation before T16.5a may
  return to `verified` or T16.5b may reopen.

## Out of scope

USB enumeration, serial or camera open, servo reads, live evidence, register
writes, torque changes, motion, policy execution, optimizer work, and paid
compute. Hardware remains closed throughout this correction.

## Authority

The prior `census_trace_conformant` capability is withdrawn until this
correction is reviewed and remotely preserved. This brief grants no live access
or physical authority.
