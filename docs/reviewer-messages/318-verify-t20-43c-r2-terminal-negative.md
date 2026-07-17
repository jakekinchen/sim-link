# Reviewer Decision 318 - Verify T20.43c-R2 Terminal Negative

**Date:** 2026-07-17

## Decision

`VERIFY_T20_43C_R2_TERMINAL_NEGATIVE`

The separately rooted ACT-on-R0 replacement completed exactly once. It is a
scientific terminal negative, not an infrastructure failure: all 10,000 finite
optimizer updates and all 14 fixed rollout evaluations completed, while no
checkpoint under either execution semantic passed strict-v2 Gate C.

## Verified evidence

- replacement marker `dfe3ff05...` consumes permit `f063e034...` from origin
  source `7bf8326...` and preserves the first continuation marker/failure;
- equivalence `fdc06297...` proves 234 float32 tensors / 51,617,414 elements
  bit-exact at maximum absolute error 0, empty AdamW state, zero optimizer
  steps, and an unadvanced seed-20260801 sampler before update 1;
- run `82a06083...` completes 10,000 finite updates, seven checkpoints, and 14
  rollout-primary evaluations;
- result `bf2c8b46...`, scorecard `6f848570...`, retention `e565e17a...`, and
  final receipt `be11a258...` reconstruct through the independent verifier;
- six learned checkpoints, 13 new rollout traces, 14 mirror/manifest pairs,
  and their complete local trees are hash-bound by the retention receipt;
- no terminal-failure artifact exists; hardware, camera, serial, physical
  motion, network, external compute, and Brev remain unused.

## Scientific interpretation

ACT learned the grasp-lift-hold-lower behavior but did not learn a complete
release cycle.

- Chunk-50 at updates 2,500, 5,000, 7,500, and 10,000 met the strict grasp,
  unassisted-lift, unsupported-hold, support-free, stable-hold, lower, and
  25 mm lift predicates.
- At update 10,000 chunk-50 lifted 37.655 mm and passed every Gate C predicate
  except `release_final_contact_clear` (measured 0, required 1). Update 7,500
  had the same sole failed predicate and lifted 40.025 mm.
- The maximum lift was 45.674 mm at update 2,500 receding-10, but that rollout
  missed grasp-hold and stable-hold by one frame each and also failed release
  and retreat clearance.
- The greatest strict-v2 frame count was 183 at update 5,000 chunk-50; it
  failed only final release and retreat clearance.
- Receding-10 did not preserve the strong chunk-50 behavior. At update 10,000
  it had zero strict grasp-hold frames and only 0.502 mm maximum lift.

This resolves ACT-on-R0: the architecture and data are sufficient for a nearly
complete long-horizon scripted chunk, but the fixed standard recipe does not
produce a strict full-cycle policy under the pre-registered evaluator. Gate C
remains failed.

## Schema note

The nested standard result and scorecard intentionally retain the unchanged
legacy `scenesmith.t20_43b_r1_act_*` schemas and task label. The R2 marker,
equivalence, retention, and final-receipt wrappers carry the distinct
T20.43c-R2 identity and bind those legacy-schema payloads to this replacement.
The complete R2 verifier passes; no evidence is relabeled or mixed with the
consumed first continuation.

## Authority disposition

Training is closed. No retry, second replacement, recipe/schedule/data/
threshold change, T20.45 activation, hardware, network, external compute,
Brev, physical transfer, promotion, or destructive operation is authorized.
The result may be folded into the reconstruction kit and frozen evaluator as a
verified negative and a release-phase counterexample.
