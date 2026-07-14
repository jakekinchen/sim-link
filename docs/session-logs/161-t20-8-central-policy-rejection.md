# Executor Session 161 - T20.8 Central Policy Rejection

T20.8 added a backwards-compatible simulation-policy acceptance path inside
the central authority composer without changing the existing v1 global
decision graph. The decision independently re-hashes and verifies the T20.6
semantic contract, strict-v2 fixture, T20.7 plan, all training results and
checkpoint bytes, all closed-loop evidence, rendered keyframes, measured gate
margins, and the signed evaluation gate.

The tracked decision is deterministic and byte-identical on rerun. It records
no selected model, zero measured strict-success rollouts versus three required,
and zero T20.7 strict successes versus one required. Therefore
`simulation_policy_accepted`, `physical_transfer_ready`, and
`promotion_eligible` all remain false. Re-signed escalation and source-drift
tests fail closed, while the previously granted T20.1 local simulation-training
authority still verifies unchanged.

The same-agent adversarial review covered stale evidence, source substitution,
graph ambiguity, double counting, repeat-threshold drift, winner fabrication,
projection/assistance omission, keyframe and margin loss, and physical or
promotion escalation. Sixty-nine relevant tests pass. No new model load,
optimizer run, rollout, hardware, physical transfer, external compute, or Brev
was used.
