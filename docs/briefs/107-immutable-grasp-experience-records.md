# Slice Brief 107 - Immutable Grasp Experience Records

**Date:** 2026-07-13

## Objective

Define the first machine-verified M17 raw-rollout and frame-record contract,
bound to the verified geometry-derived MuJoCo grasp without inventing missing
actions, physical measurements, or training eligibility.

## Contract

- Define versioned raw-rollout and frame-record schemas with stable IDs,
  nanosecond timestamps, prompt identity, source class, proof mode, task phase,
  control mode, controller owner, coordinate/preprocessing lineage, object and
  workcell identity, and content-addressed source evidence.
- Use canonical task phases while retaining source phase names separately;
  `recovery` is a control mode and is forbidden as a task phase.
- Keep requested, proposed, projected, sent, and measured actions separate.
  Every action is either observed with ordered names, representation, units,
  finite values, and provenance, or explicitly unavailable with a reason.
- Keep requested/achieved gripper pose, contact witness, aperture, effort,
  reward components, progress, and strict-evaluator result separately sourced.
- Define hard-boundary events and prohibit reward, progress, future state, or
  privileged simulator fields from actor-input declarations.
- Project a minimal fixture from the signed T19.0l artifact. Preserve its known
  phase/contact outcomes, mark absent action/pose/effort observations missing,
  and require quarantine rather than calling the fixture training-ready.
- Fail closed on duplicate/out-of-order frames, hash drift, unknown enums,
  missing prompt/owner/units/provenance, invented unavailable values, source
  linkage drift, and actor-input leakage.

This slice may establish immutable record-contract validity. It may not compile
Parquet tables, open the training lock, run an optimizer, or access hardware.

## Verified Outcome

- Signed contract identity `f2b8b462ec5b153c6e5366a10f85a1e6ebf99c580b2eaf3b94e33f7d88226ab6`;
  file SHA-256 `4214679b11c22ba147d7e874d149043e26b8bdad188e0348b6d2d5bb53a11dad`.
- The fixture rollout `rollout-af554fa23d42d986ea3a4e06` is bound to the
  T19.0l grasp, simulation twin profile, and SO-101 coordinate contract.
- Two source-projection frames map `grasp_hold` to `grasp_confirmed` and
  `unsupported_lift_hold` to `stable_hold`; source phase names remain explicit.
- All five action variants are `not_observed`, per-frame requested/achieved
  gripper pose and effort are absent, and segments/windows/normalization are not
  compiled. Five explicit reasons quarantine the fixture from training.
- Twelve focused tests pass in each configured runtime; deterministic writer,
  compilation, JSON, and diff checks pass; the 210-test broad gate passes.
