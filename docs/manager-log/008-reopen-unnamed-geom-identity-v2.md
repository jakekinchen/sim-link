# Manager Intervention 008 - Reopen Unnamed Geom Identity V2

**Date:** 2026-07-10

## Decision

`REOPEN T16.3`

## Evidence

Reviewer decision 032 accepted commit `07a652e` after 21 focused and 46 broad
tests passed. Independent adversarial fixtures then reproduced two violations
of brief 020's order-invariant exit condition:

1. Two unnamed collision geoms with physically equivalent quaternion spellings
   (`0.5 0.5 0.5 -0.5` and `1 1 1 -1`) received different semantic identity
   stems. Comparison-time quaternion canonicalization never ran because the
   records had already become missing/extra under different keys.
2. Two unnamed geoms sharing one structural stem but carrying different
   friction values retained XML sibling order within the group. Reversing the
   siblings swapped the `#1` and `#2` records in both collision and friction
   extraction.

The existing suite covered different structural stems and literally identical
duplicates, but not equivalent quaternion identity inputs or same-stem records
with different contact semantics. Passing those tests was therefore necessary
but insufficient.

## Resolution Required

- Canonicalize explicit quaternion values before unnamed-geom identity hashing.
- Sort each same-stem group by a canonical serialization of its complete
  normalized explicit attributes before assigning occurrence suffixes.
- Reuse canonical quaternion values in that secondary sort and retain `class`
  plus all non-identity attributes so contact semantics remain attached.
- Add direct regressions for equivalent scaled/sign quaternion spellings,
  reordered duplicates with explicit friction, and reordered duplicates whose
  friction is inherited from different classes.
- Bump the recorded identity strategy to v2 and regenerate the content-addressed
  structural-diff artifact.

Reviewer decision 032 and its T16.3 closeout are superseded. Brief 021 is
deferred; no measured-mass work may begin until brief 022 passes fresh review.
