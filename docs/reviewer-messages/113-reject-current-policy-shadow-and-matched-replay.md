# Reviewer Decision 113 - Reject Current Policy Shadow And Matched Replay

**Date:** 2026-07-13

## Decision

`ACCEPT DIAGNOSTIC EXECUTION; REJECT POLICY SHADOW, MATCHED REPLAY, AND MOTION`

The complete Brief 087 evidence independently binds accepted bracket session
`t16-5c-20260713-0958-cdt`, reviewed stable-camera roles, final retained frames,
exact `q_after`, exact prompt, pinned processor, pinned checkpoint revision and
weight hash, fixed inference noise, postprocessed action chunk, canonical
coordinate transform, and three deterministic MuJoCo replay prefixes.

Fresh same-agent review checked private-frame leakage, camera-role reversal,
q-before/q-after substitution, processor or weight substitution, silent random
model fallback, network access, stochastic proposal drift, normalized versus
postprocessed action confusion, coordinate clamping, contact identity, horizon
prefix reuse, simulator warning loss, physical-command leakage, and authority
escalation. The first failed inference attempt is not counted as evidence: it
completed model inference but failed the pinned postprocessor input adapter.
The repaired execution reloaded the strict checkpoint, repeated inference
twice exactly, successfully postprocessed, and wrote one immutable diagnostic.

The diagnostic facts are useful and adverse. Wrist roll is outside the
checkpoint's observed state support. The first proposed wrist-roll change is
54.4099 degrees, and full-chunk per-axis deviations reach 55.8645 degrees on
wrist roll and 51.5712 degrees on elbow flex. The measured starting pose cannot
be represented by the current physical-to-MuJoCo mapping without clamping
shoulder lift and elbow flex. All 5/10/15 prefixes preserve shoulder/lower-arm
self-contact. Finally, the canonical sorting simulator contains the red/blue
task scene that is absent from the accepted physical camera observation.

This accepts only
`physical_pi05_model_ready_tensor_diagnostic_observed`,
`physical_pi05_no_actuation_diagnostic_proposal_observed`, and
`pi05_proposal_prefix_control_replay_diagnostic_observed`. It withholds accepted
live policy input, `policy_shadow_input_valid`, accepted policy shadow, matched
MuJoCo replay, `safe_enough_to_prepare_t16_6`, all motion stages, twin
qualification, simulation-training authority, optimizer work, Brev, and paid
compute. T16.5c remains in progress. The next experiment is an offline
coordinate-contract and collision reproduction using the measured pose; no
physical motion is justified.
