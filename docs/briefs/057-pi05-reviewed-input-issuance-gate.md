# Slice Brief 057 - PI0.5 Reviewed Input Issuance Gate

**Date:** 2026-07-11

## Objective

Implement and verify, entirely offline, a fixture-only signed gate that defines
how the three inputs withheld by Brief 056 can later be reviewed and composed
without letting self-signed, synthetic, stale, mismatched, or partial evidence
authorize production PI0.5 preprocessing.

## Contract

- Reverify the checked-in Brief 056 preprocessing source contract and require
  its exact `blocked_missing_inputs` identity, local capability, authority
  denials, and no-execution facts.
- Define strict signed input schemas for a live-session review acceptance
  decision, a stable-camera role binding, and a reviewed task prompt. Every
  input must identify its evidence class, issuer, subject, scope, source
  identities, review record, issuance time, and finite validity interval.
- A live-session acceptance decision may reference only an actual tracked Brief
  055 review manifest with `candidate_observed_pending_review`; fixture or
  failure evidence, an absent manifest, a self-declared acceptance without a
  bound reviewer record, or a changed source must fail closed.
- A camera-role binding must assign exactly the two stable camera identities
  pinned by Brief 056 bijectively to `observation.images.top` and
  `observation.images.wrist`. Reject numeric indexes, raw camera/device names,
  duplicate identities or roles, unknown identities, missing private-review
  evidence hashes, and session/source mismatch.
- A task review must bind one nonblank bounded UTF-8 task to the exact PI0.5
  cleaning and prompt-template semantics. Reject control characters, multiline
  or underscore ambiguity, normalization drift, empty tasks, and unreviewed or
  differently scoped prompts.
- Compose the three inputs only when all subjects, source-contract identity,
  accepted-session identity, camera identities, issuer allowlists, scopes,
  evidence classes, review records, and validity windows agree. Fixture inputs
  may prove gate conformance only and must never become production inputs.
- Emit and independently verify one deterministic checked-in
  `blocked_missing_reviewed_inputs` artifact with all three inputs absent. It
  may grant only `pi05_reviewed_input_issuance_gate_conformant` and must retain
  all Brief 056 authority denials.
- Add adversarial tests for re-signed authority escalation, evidence-class
  substitution, issuer/scope/subject/session/source drift, stale/future/invalid
  time windows, camera-role ambiguity, task normalization ambiguity, path
  escape/aliasing, malformed numeric fields, and partial-input promotion.

## Evidence and authority

Do not create or accept a real live-session decision, camera-role assignment,
or task prompt in this slice. Do not construct a tokenizer, processor, model,
or policy input; do not read model weights, preprocess, infer, replay, access
hardware, call Studio, reconnect, write, change torque, command motion, train,
or start paid compute. The live gate and training lock remain closed.
