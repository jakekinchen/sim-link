# Reviewer Decision 181 - Verify T20.20 Observer-Role Evaluator Contract

`CONTINUE_T20_21_THIN_PAIRED_TRACE_RUNNER`

Reviewed Brief 151 through implementation commit `50abb80`.

The signed contract binds strict-v2 identity `950e7568...` and gives the
simulator-privileged and hardware-observable roles the same eight ordered task
predicates. Their input schemas remain disjoint: simulator geometry, contact,
object, and safety state cannot enter the observable role, while missing
observable events become explicit non-successful `not_observed` results.

The signed consistency report passes one complete positive and one
stable-hold-negative parity case. Both observable cases are explicitly
`simulator_fixture_projection`; they are schema/semantic tests, not hardware
observations. Privileged-field injection, claimed-success injection,
camera/VLM sources, re-signed contract expansion, evaluator-to-actor leakage,
non-finite values, and duplicate phase evidence are rejected.

Same-agent adversarial review checked authority escalation, stale strict-v2
binding, threshold and allowlist mutation, role and actor leakage, missing
evidence, event spoofing, evidence-source relabeling, non-finite values,
deterministic identity, path scope, and cleanup side effects. Thirty-seven
focused tests and a 97-test relevant broad gate passed; the checked artifact
reverified exactly.

T20.20 is verified only as a local observer-role evaluator contract and
simulator consistency fixture. It grants no hardware observation, camera/VLM
access, physical success or qualification, optimizer, training readiness,
policy acceptance, physical transfer, promotion, actuation, external compute,
or Brev authority. Continue to T20.21's offline thin paired trace runner.
