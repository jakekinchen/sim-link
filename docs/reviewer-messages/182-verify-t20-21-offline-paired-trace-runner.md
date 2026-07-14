# Reviewer Decision 182 - Verify T20.21 Offline Paired Trace Runner

`CONTINUE_T20_22_TIMING_LATENCY_CERTIFICATE_V0`

Reviewed Brief 152 through implementation commit `7f264ab`.

The runner accepts exactly one signed simulator-privileged trace and one signed
hardware-observable-schema trace. It binds exact `q0`, clock identities,
strictly increasing nanosecond timestamps, joint samples, distinct proposed,
issued, and measured actions, and fixed task events. Trace-internal `q0`
consistency and cross-trace alignment gate downstream comparison; clock
identity additionally gates event-time comparison.

The matched synthetic pair has zero joint/action/event-time error. Nine fixed
diagnostics route `q0`, length, proposed, clock, issued, measured, joint,
event-presence, and event-time mismatches without selecting a cause, calibration
change, or twin update. The observable-schema trace is explicitly synthetic,
not a hardware observation.

Same-agent adversarial review covered false `q0`, trace aliasing, action
relabeling, missing/unknown fields, signed mutation, non-finite/wrong-width
vectors, frame-index and timestamp ambiguity, duplicate events, pixel and
privileged leakage, clock mismatch, premature downstream comparison, contract
re-signing, input mutation, and authority escalation. Seventeen focused tests
and a 105-test relevant broad gate passed; the checked artifact reverified.

T20.21 is verified only as synthetic offline paired-trace runner fixture
conformance. It grants no hardware observation or execution, paired real/sim
claim, clock synchronization, calibration/twin update, physical qualification,
policy acceptance, physical transfer, promotion, actuation, external compute,
or Brev authority. Continue to T20.22's offline timing/latency certificate.
