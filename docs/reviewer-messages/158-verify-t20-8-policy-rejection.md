# Reviewer Decision 158 - Verify T20.8 Policy Rejection

`CONTINUE`

Reviewed implementation boundaries `bc5f008c86737b43058472288e21a75fff48cc92`
and `528d3851c81256418526c3a3e9ac4031b4e5539a`, plus tracked decision artifact
commit `c4a2643b255c26863ddd65e8c6296fb6de0df44f` and identity
`0587820043c6f2f21a05e22b95062dc4f4187a72513ceb56ca3ce21d65b59ace`.

The central composer independently verifies the T20.6 semantic and strict-v2
fixtures, T20.7 plan, training gate, four result/checkpoint pairs, four
closed-loop results with keyframes and gate margins, and the signed evaluation
gate. Recomposition is deterministic and fails closed on source drift or a
re-signed winner, success count, repeat threshold, projection count, physical
transfer, or promotion escalation. The existing v1 authority graph and live
T20.1 local-simulation training grant still verify unchanged.

Current evidence has no selected model, zero strict successes versus three
required, and zero T20.7 strict successes versus one required for selection.
The decision correctly records `simulation_policy_accepted: false`,
`physical_transfer_ready: false`, and `promotion_eligible: false`. Exact-pass
margins are normalized to `0.0`; failed gates retain explicit signed deficits.
Sixty-nine relevant authority, training, evaluation, strict-grasp, rollout,
and pointer tests pass.

Verify T20.8 as a truthful rejection. Continue only to a new causal diagnostic
that tests the recorded expert action sequence through the exact policy rollout
adapter before another training hypothesis. Do not accept a model, claim M20
capability, start residual RL, or grant hardware, physical transfer, promotion,
external-compute, or Brev authority.
