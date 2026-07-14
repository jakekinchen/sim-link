# Slice Brief 126 - T20.6 Adversarial Outcome-Versus-Strict Evaluation

**Date:** 2026-07-14

## Objective

Bind truthful terminal outcomes to the existing strict-v2 grasp semantics so a
cube reaching its target cannot be relabeled as strict success unless the full
ordered approach, contact, grasp, lift, transport, placement, release, and
retreat witness passes.

## Contract

- Reuse the checked-in strict-v2 evaluator and deterministic positive trace;
  do not create a second success definition.
- Emit one signed, deterministic, source-bound fixture with an explicit
  capability-stage projection and terminal outcome recorded independently from
  `strict_grasp_success`.
- The positive case must pass the same evaluator with all ordered witnesses and
  bounds intact.
- Include named putt, planar-slide, ballistic-throw, terminal-occupancy-only,
  scripted-motion, assistance-relabel, stage-drift, and actor-privilege cases.
  Each negative must preserve any truthful target occupancy while failing strict
  success for its expected semantic reason.
- Bind the source strict-v2 fixture identity and reject missing, stale,
  contradictory, non-finite, or identity-drifted evidence.

## Acceptance Criteria

- The artifact verifies byte-for-byte from deterministic sources and the
  checked-in strict-v2 fixture remains unchanged and valid.
- The positive case exposes the complete eight-stage witness and passes strict
  semantics without claiming pure-policy or MuJoCo success.
- Every required adversarial case records its truthful terminal outcome,
  rejects strict success, and contains its expected failure reason.
- Focused semantic, artifact, pointer, and authority tests pass, followed by a
  fresh same-agent adversarial review.

## Out Of Scope

Model training or inference, policy comparison, MuJoCo capability claims,
hardware, physical transfer, promotion, external compute, and Brev.

## Verified Outcome

The source-bound deterministic fixture projects the checked-in strict-v2 trace
onto all eight capability stages. Its analytic positive reaches the declared
target and passes strict semantics while remaining explicitly non-policy and
non-MuJoCo evidence. Eight required adversarial traces also reach and stably
occupy the target, yet putt, slide, throw, invalid release, scripted motion,
assistance relabeling, stage drift, and actor privilege each fail strict success
for the expected reason. Fifty-six focused semantic, artifact, authority, and
pointer tests pass. Reviewer 155 accepts implementation boundary `fd4b2a4`.
