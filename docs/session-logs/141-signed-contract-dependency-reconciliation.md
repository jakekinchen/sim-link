# Session 141 - Signed Contract Dependency Reconciliation

**Date:** 2026-07-13
**Branch:** `codex/pi05-autolearn-loop`
**Parent:** `f0402f16aa8fcef7904eee7ed979b3671d7cb77f`
**Maintenance commit:** `f6626faeaadd6cbfb86e000cbf15e750772c20e1`

## Scope

The T17.1 maintenance refresh changed the immutable experience-record
identity. The signed T17.2 processor contract and T17.3 normalization bundle
still referenced the prior identity, which made their canonical verification
fail closed. This session rebound both artifacts through their existing
builders; it did not change processor behavior, normalization statistics,
proof scope, or authority.

## Evidence

- T17.2 processor identity is now
  `59827b3dfe8adce0903495edd9f68af2db5f40abf93aa0fb51b9acfcef4118c7`;
  file SHA-256 is
  `3145f4ae1efb86463df2398775315cd0b764a74bca954448c6a1d0f57eb8f503`.
- T17.3 normalization identity is now
  `dea3ff8cb85640499416fc6fd6bf0cf43dce3479766fb1ff277e8d224e097ebe`;
  file SHA-256 is
  `0d20428fbe20a27d0c60ad9f8b75ce3613a01f244aa6771e21fa474913ea3bda`.
- Canonical processor and normalization writers pass `--verify`.
- Processor round-trip count remains 128 with maximum error
  `4.440892098500626e-16`; normalization sample count remains 94,568 and
  `production_eligible` remains false.
- The T17.4 compiler was rebound to the new normalization identity after this
  maintenance commit; its output remains training-ineligible and quarantined.

## Safety boundary

No raw rollout bytes were rewritten. No normalization was applied to rollout
frames. No training, optimizer, hardware, physical motion, Brev, or paid
compute occurred.
