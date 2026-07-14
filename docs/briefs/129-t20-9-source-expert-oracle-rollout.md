# Slice Brief 129 - T20.9 Source-Expert Oracle Rollout

**Date:** 2026-07-14

## Objective

Feed the immutable seed-2 held-out expert action sequence through the exact
T20.7 policy closed-loop scene, action-application, phase, and evaluation path
to determine whether the execution adapter can reproduce the recorded strict
grasp before any new optimizer hypothesis.

## Contract

- Resolve seed 2 only through the verified T17.5b episode-store manifest,
  verify the raw episode bytes and record contracts, and bind the source
  rollout, frame, grasp, and action-sequence identities.
- Supply each source `actions.requested` vector through the same six-value
  policy callback used by T20.7. Use the same reset scene, 244-frame phase
  schedule, actuator ranges, clipping detection, MuJoCo stepping, strict-v2
  evaluator, five 256 px keyframes, and measured-versus-threshold margins.
- Record source-versus-oracle action, joint-position, joint-velocity, phase,
  and object-position deltas per phase, including the first divergence above
  declared finite tolerances. Do not hide a mismatch behind aggregate pass
  counts.
- Classify the result mechanically: a strict oracle pass with no projection or
  assistance proves the adapter can execute the source trajectory and
  localizes T20.7 failure to learned action prediction; an oracle failure
  blocks further training until the first execution divergence is corrected.

## Acceptance Criteria

- The oracle consumes exactly 244 immutable source actions in source order,
  with no model load, inference, optimizer step, action replacement, or
  geometry-controller call during rollout.
- The signed artifact is deterministic and independently verifiable from the
  T17.5b source bytes; source mutation, action reordering, wrong seed, phase
  drift, non-finite values, projection, and evidence escalation are rejected.
- The artifact retains five rendered keyframes and all strict gate margins,
  plus explicit measured maxima and thresholds for source-versus-oracle state
  divergence.
- Same-agent review checks temporal alignment, pre-action versus post-action
  comparison, coordinate representation, clipping, source substitution,
  nondeterminism, and false policy-capability claims.

## Out Of Scope

Model loading, inference, optimizer training, dataset mutation, policy
acceptance, residual RL, hardware, physical transfer, promotion, external
compute, and Brev.
