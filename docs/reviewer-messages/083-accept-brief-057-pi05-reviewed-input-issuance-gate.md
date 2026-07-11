# Reviewer Decision 083 - Accept Brief 057 PI0.5 Reviewed-Input Issuance Gate

**Date:** 2026-07-11

## Decision

`CONTINUE T16.5C; ACCEPT BRIEF 057 PI0.5 REVIEWED-INPUT ISSUANCE GATE; LIVE GATE CLOSED`

Implementation `44dd871745efcc3490321a3ada92b4ddf138ba6c` is present on
`origin/codex/pi05-autolearn-loop`.

The gate fully reverifies the exact Brief 056 source contract before considering
any reviewed input. It defines distinct signed schemas for a future live-session
acceptance decision, stable-camera role binding, and task-prompt review. Each
input is restricted to an exact tracked path and field set, one allowlisted
issuer, one reviewer decision record with machine-readable subject markers, one
source-contract and session identity, and a positive bounded validity interval.

The live-session input must bind an unchanged candidate-pending-review Brief 055
manifest. The camera input must bind the same manifest and bijectively assign
the two pinned stable identities to top/base and wrist/left-wrist without raw
camera identities or numeric indexes. The task input must be bounded, NFC,
single-line, underscore-free, control-free, and hash-bound to the exact PI0.5
task key, prompt template, and prefix semantics.

Fixture and production review classes cannot mix. Complete fixture inputs prove
only gate conformance; complete production-class inputs can expose only the
local `pi05_reviewed_input_bundle_valid` capability for a later stage. Even that
state does not build or accept a policy input. Partial bundles remain blocked,
and re-signing any source, class, role, task, time, review record, execution
fact, proof label, or authority field fails equality with the verified sources.

The checked artifact contains no reviewed inputs or evaluation time. It remains
`blocked_missing_reviewed_inputs`, records all three exact missing inputs, has
no proof labels, and grants only
`pi05_reviewed_input_issuance_gate_conformant`. No live-session acceptance file,
camera-role file, or task-prompt file exists in the repository.

The complete diff was reviewed for global-authority escalation, self-signed
review forgery, evidence-class substitution, source/session ambiguity, stale or
future evidence, path aliasing, Unicode/control ambiguity, raw camera leakage,
partial promotion, unsafe defaults, and documentation drift. One hundred
twenty-three focused tests pass in each robotics runtime. The source and gate
writers verify in both runtimes, and the 322-test regression gate passes in
69.292 seconds.

Grant only `pi05_reviewed_input_issuance_gate_conformant`. Do not grant a real
reviewed-input bundle, accepted live policy input,
`static_pose_bracketed_observation`, `policy_shadow_input_valid`, processor or
model construction, model-weight load, preprocessing, inference, policy shadow,
replay, actuation, physical qualification or transfer, promotion, or training
authority.

The next slice may remain offline and prove fixture-only preprocessing
conformance, or it may wait for all three independently reviewed real inputs.
Neither path may treat the temporary adversarial fixtures as live evidence or
reopen hardware in this parent thread.
