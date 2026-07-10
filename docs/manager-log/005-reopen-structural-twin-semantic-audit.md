# Manager Intervention 005 - Reopen Structural Twin Semantic Audit

**Date:** 2026-07-10

## Decision

`CORRECT THEN CONTINUE`

## Evidence

- Brief 012 requires the structural artifact to consume the checked-in twin
  profile identity, but commit `7bebf55` binds only the dependency lock and XML
  source hashes.
- Quaternion fields are compared as raw numeric arrays. Equivalent rotations
  with different scale or sign are therefore reported as physical mismatches.
- An absent MuJoCo `<option>` becomes a missing record instead of a comparison
  against effective defaults.
- Bodies whose mass is inferred from geoms, including the Menagerie camera
  mount, disappear from the inertial comparison instead of becoming explicit
  unknown evidence.
- Friction extraction reports hard-coded default declarations without proving
  that the defaults are attached to the compared joints or geoms.
- Existing tests prove deterministic regeneration and signed-record tampering,
  but not twin-profile drift, actual source-byte drift, semantic quaternion
  equivalence, effective defaults, or inferred-inertia unknowns.

## Resolution Required

Return T16.3 to `in_progress`. Preserve commit `7bebf55` as the first mechanical
baseline, then correct the semantic comparison in a new commit. The corrected
artifact must retain raw source evidence while comparing canonical/effective
values, bind the twin profile identity, surface unsupported inferred quantities
as `unknown`, and add focused regression tests for each issue above.

Reviewer decision 027 is superseded. T16.4 must not start until a fresh reviewer
accepts the corrected T16.3 artifact.
