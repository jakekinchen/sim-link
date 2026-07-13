# Slice Brief 108 - Canonical SO-101 Processor

**Date:** 2026-07-13

## Objective

Implement one named SO-101 processor shared by later collection, compilation,
training, evaluation, and adapters without hiding validation or safety limiting
inside coordinate conversion.

## Contract

- Fix the canonical ordered joints to shoulder pan/lift, elbow flex, wrist
  flex/roll, and gripper. Reject missing, extra, permuted, boolean, or non-finite
  values.
- Support only explicit absolute action mode for the first contract. Reject
  delta/relative ambiguity.
- Implement pure MuJoCo-radian/gripper-radian to canonical LeRobot-degree/
  gripper-percent conversion and its inverse with no clamping or projection.
- Implement range validation as a separate fail-closed operation in either
  representation.
- Implement safety limiting as a separate operation that returns requested and
  executed values, clipped indices/names, and whether limiting occurred. Never
  mutate the requested input.
- Emit a signed processor contract bound to T17.1 and the SO-101 coordinate
  identity, including formulas, ranges, golden poses, gripper monotonicity, and
  deterministic randomized round-trip evidence.
- Test permutation, round trip, bounds, action mode, unclamped transform,
  gripper monotonicity, golden-pose parity, non-finite rejection, and limiting
  provenance in both configured runtimes.

This slice may establish canonical processor validity. It may not establish a
normalization bundle, compiled training frames, training readiness, optimizer
authority, or physical actuation.

## Verified Outcome

- Processor `scenesmith_so101_canonical_processor_v1` is signed as artifact
  `9800c873896eee63c10da7a4c02c964ff1faf28711d438c89731f3266d77a6f2`;
  file SHA-256 `cd60dce9f791f4c8becf7d33baa2382d96b843fe0af5b975a0ea0f796505d902`.
- Pure transform leaves a requested 120% gripper value unclamped at 2.129302
  rad; validation rejects it; the separate limiter records requested 120%,
  executed 100%, and clipped joint `gripper`.
- 128 deterministic in-range round trips have maximum error
  4.4408920985e-16. The golden pose matches the legacy in-range mapping and the
  gripper transform is monotonic from 0% to 100%.
- Eleven focused tests pass in both configured runtimes; deterministic writer,
  compilation, JSON, and diff checks pass; the 221-test broad gate passes.
