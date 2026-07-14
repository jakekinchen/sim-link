# Executor Session 158 - T20.6 Outcome-Versus-Strict Evaluation

T20.6 added a deterministic source-bound layer over the existing strict-v2
grasp evaluator. The positive analytic trace projects onto all eight capability
stages, performs a bounded 12 mm lateral transport into the declared target,
and passes strict semantics without being relabeled as policy or MuJoCo proof.

Eight adversarial traces also end with stable target occupancy. Putt, planar
slide, ballistic throw, invalid release, scripted object motion, controller
assistance relabeled as policy, missing stage evidence, and evaluator-state
leakage all fail strict success for their expected reason. Terminal outcome and
strict success remain separate signed fields.

The artifact regenerates byte-identically and binds strict-v2 identity
`950e7568...`. Fifty-six semantic, artifact, authority, and pointer tests pass.
No optimizer, model inference, hardware, network, external compute, or Brev was
used. T20.6 closes as verified evaluator evidence, not policy capability.
