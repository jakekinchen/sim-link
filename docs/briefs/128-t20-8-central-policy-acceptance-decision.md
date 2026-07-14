# Slice Brief 128 - T20.8 Central Policy-Acceptance Decision

**Date:** 2026-07-14

## Objective

Issue the simulation-policy acceptance decision through the central authority
composer without changing or invalidating its existing v1 global-decision graph
or the live T20.1 simulation-training grant.

## Contract

- Consume and independently verify the T20.6 outcome-versus-strict fixture,
  strict-v2 fixture, T20.7 plan, common-sample training gate, all four training
  results and checkpoint hashes, all four closed-loop results, and the T20.7
  evaluation gate.
- Add a backwards-compatible policy-acceptance decision path inside
  `authority_composer.py`; no component artifact may grant the system decision.
- Acceptance requires one selected checkpoint with at least three independent
  policy-owned strict-v2 successes, zero projection, zero assistance, required
  keyframes, and complete measured-versus-threshold margins. A missing winner,
  zero strict success, insufficient repeats, or contradictory source fails
  closed with explicit measured and required values.
- Keep `physical_transfer_eligible`, `promotion_eligible`, and physical
  authority false because M19 evidence is absent, independent of simulation
  policy acceptance.

## Acceptance Criteria

- The decision is signed, deterministic, source-bound, and byte-identical on
  rerun from the same evidence.
- The current evidence mechanically yields
  `simulation_policy_accepted: false`, selected model `null`, measured strict
  successes `0`, required repeat successes `3`, and a stable denial reason.
- Tests reject a re-signed winner, success count, repeat threshold, projection,
  source identity, physical-transfer, or promotion escalation.
- Same-agent review checks stale evidence, graph ambiguity, authority
  escalation, double counting, evaluation leakage, keyframe/margin loss, and
  contradictions with T20.7 or the live T20.1 grant.

## Out Of Scope

New model loads, optimizer training, another rollout, dataset mutation,
hardware, physical transfer, promotion, external compute, Brev, and changes to
the existing v1 central-authority contract or T20.1 authority artifacts.
