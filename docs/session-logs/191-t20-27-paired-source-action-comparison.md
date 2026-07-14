# Session Log 191 - T20.27 Paired Source-Action Comparison

## Scope

Brief 158 composed an offline paired comparison from the four verified T20.26
batch artifacts and the exact held-out seed-6 source action. No model inference,
rollout, action application, optimizer, hardware, camera, external compute, or
Brev was used.

## Evidence And Result

- Gate identity:
  `37c7fb8fb2899e3c368cc5c25a2e3f0a0b8526a43477b979632edc850fd9eabe`.
- Paired inference seeds: 5.
- Clean source-action MAE: 0.50833 rad.
- Recovery source-action MAE: 0.61926 rad.
- Recovery-minus-clean delta: +0.11094 rad.
- Seed result: 0 improved, 5 regressed, 0 tied.

Per-joint recovery-minus-clean MAE is +0.00195 shoulder pan, +0.18749 shoulder
lift, +0.07576 elbow flex, +0.17851 wrist flex, +0.22311 wrist roll, and
-0.00120 gripper. Recovery supervision therefore does not improve the paired
frame-zero source-action distribution; its tiny gripper improvement is
overwhelmed by arm regressions.

## Validation

Eighty-one relevant tests passed. Same-agent review covered source identity,
duplicate-process equality, sample/seed/joint order, finiteness, pairing,
requested-action coordinates, signed mutation, authority, and cleanup.

This result is bounded to one identical frame-zero observation over five
declared inference seeds. No significance, closed-loop capability, policy
acceptance, or further-training claim is made.
