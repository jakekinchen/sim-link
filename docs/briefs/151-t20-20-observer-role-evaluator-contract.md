# Slice Brief 151 - T20.20 Observer-Role Evaluator Contract

**Date:** 2026-07-14

## Objective

Define and falsify a versioned strict-v2 task-predicate contract shared by a
simulator-privileged evaluator and a hardware-observable evaluator, while
proving that missing observations and privileged-field leakage fail closed.

## Contract

- Bind the immutable strict-v2 evaluator identity and preserve one identical,
  ordered task-predicate vocabulary across both roles.
- The privileged role may consume declared simulator-only geometry, contact,
  object-pose, and table-contact evidence. The observable role may consume only
  declared timestamp, task phase, measured joint/action, aperture, effort, and
  externally observed task-event fields; it must reject every privileged field.
- Every predicate result records its role, evidence availability, truth value,
  and reason. Missing required evidence is `not_observed`, never inferred,
  defaulted positive, or silently treated as simulator truth.
- The observable role is an evaluation surface only. It is not an actor input,
  camera/VLM evaluator, physical qualification, calibration update, or authority
  source.
- Produce a signed simulator consistency report over fixed positive and
  negative cases. Agreement means the two roles implement the same predicate
  vocabulary on complete, deliberately equivalent evidence; it does not prove
  the observable inputs exist on hardware or that the physical twin qualifies.
- Do not access hardware or cameras, instantiate a live robot object, run an
  optimizer, modify prior strict-v2 artifacts, start external compute or Brev,
  or grant training readiness, policy acceptance, physical transfer, or
  promotion.

## Acceptance Criteria

- Tests first cover vocabulary identity, positive and negative parity,
  anti-false-positive cases, missing-observation failure, malformed/non-finite
  values, privileged-to-observable role leakage, observable-to-actor leakage,
  duplicate/unknown fields, deterministic signing, and authority escalation.
- Both roles emit the same ordered predicate keys and explicit availability;
  the observable role cannot receive or derive simulator-only evidence.
- A signed fixture and consistency report bind strict-v2 and contain fixed
  positive, negative, missing-observation, and role-leakage cases.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commit, and
  remote branch agree before T20.20 is described as verified.

## Out Of Scope

Camera or VLM evaluation; physical reads or motion; live trace collection;
paired trace comparison; timing/latency certification; calibration or posterior
inference; optimizer training; dataset mixture freeze; physical qualification;
physical transfer; promotion; external compute; or Brev.
