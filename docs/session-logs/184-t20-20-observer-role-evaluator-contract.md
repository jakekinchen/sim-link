# Session Log 184 - T20.20 Observer-Role Evaluator Contract

## Scope

Brief 151 defined one strict-v2-bound predicate vocabulary across a
simulator-privileged role and a hardware-observable role. All evidence was a
local deterministic simulator fixture. No hardware, camera, VLM, model,
optimizer, external compute, or Brev was used.

## Implementation And Result

- Both roles emit the same eight ordered task predicates: phase sequence,
  antipodal grasp, lift clearance, stable hold, relative drift, release,
  retreat, and safety limits.
- The privileged role accepts declared simulator contact, geometry, object, and
  safety measurements. The observable role accepts only timestamps, measured
  joint/action/aperture/effort channels, explicit external task-event
  observations, evidence source, and actor-input metadata.
- Missing predicate observations become `not_observed` and false. Unknown
  fields, camera/VLM evidence, re-signed allowlist changes, claimed-success
  injection, privileged-field leakage, non-finite measurements, duplicate
  phases, and evaluator-to-actor leakage fail closed.
- Complete positive and stable-hold-negative cases produce identical predicate
  values across roles. The observable cases use
  `simulator_fixture_projection`; no physical observation is claimed.

## Evidence

- Strict-v2 source identity:
  `950e7568025f4fe09b9e51633da71b3ee90212ee5ea9c86be8194863cea2e640`.
- Evaluator contract identity:
  `5b8cfcc93609e6b5393b4ced1dc18156fd6eaaf0743fd3304fc4d093fd80b039`.
- Signed simulator consistency report identity:
  `9948958468a7631c69b571bf7b366ac894ec49fe3a428fef0839cdca9b767935`.
- Tracked fixture identity:
  `560480c705a3b3ec9e98fc1a74bb0d1112b7f973fc8877b272b08597d2abb4e1`.
- Implementation commit: `50abb80`.

## Validation And Review

Thirty-seven focused semantic/record tests passed. The relevant broad gate then
passed 97 tests covering observer roles, strict-v2, phase semantics,
exact-state/experience contracts and compilation, authority composition,
artifact writing, documentation, and canonical pointers. The artifact writer
reverified the checked fixture exactly.

Same-agent adversarial review covered authority escalation, threshold and
allowlist re-signing, missing observations, claimed-success spoofing,
role leakage in both evaluator and actor directions, evidence-source
mislabeling, non-finite values, duplicate phases, synthetic-versus-physical
proof confusion, deterministic signing, path scope, and cleanup side effects.

## Result

Reviewer Decision 181 verifies only local observer-role evaluator fixture
conformance and simulator parity on deliberately equivalent evidence. It does
not verify hardware-observable inputs, physical success, physical
qualification, policy acceptance, or training readiness. T20.21 is next.
