# Manager Intervention 006 - Complete Quaternion Semantic Coverage

**Date:** 2026-07-10

## Decision

`CORRECT THEN CONTINUE`

## Evidence

Commit `fb54e64` correctly canonicalizes quaternion scale and sign for joint
frames, cameras, and named sites, and it correctly compares effective solver
defaults. The same comparison is not applied to arm or gripper collision
records.

The regenerated artifact still reports quaternion deltas for five arm collision
records whose raw pairs are scale-equivalent rotations, including
`[0.5, 0.5, 0.5, -0.5]` versus `[1, 1, 1, -1]`. A direct regression also shows
an omitted quaternion does not compare equal to MuJoCo's implicit identity
rotation.

## Resolution Required

Keep `fb54e64` as valid partial evidence, but do not call quaternion semantics
closed. Apply the same field-aware canonicalization to every transform-bearing
category, resolve an omitted quaternion to the effective identity where that is
the MuJoCo default, and add category-wide scale/sign/implicit-identity tests.
Use a documented numeric tolerance so representation noise does not create a
physics difference while true pose changes remain visible.

Brief 016 remains queued after this correction. T16.3 stays `in_progress`.
