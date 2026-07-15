# Reviewer Decision 206 - Verify T20.35e Channel Classification

**Decision:** `ACCEPT_T20_35E_MULTI_CHANNEL_CORRECTION`

## Reviewed Boundary

Brief 171, implementation and artifact commit `292a109`, verifier correction
`3013ded`, immutable T20.35d report `13b08e70...`, signed correction
`f2a8aa80...`, focused and relevant tests, canonical state, and scoped diff
were reviewed together.

## Adversarial Findings

- The correction binds the exact T20.35d report identity and revalidates its
  366 threshold coordinates, per-joint counts, boundary count, original
  classification, and original route without rewriting any source evidence.
- Ranking is deterministic: descending exceedance count then joint index.
  Wrist roll ranks first with 164; gripper ranks second with 121.
- Wrist roll alone is 44.81%, below the 50% single-joint threshold. Boundary
  errors remain 9.29%, below the 60% boundary threshold. Together wrist roll
  and gripper hold 285/366 exceedances (77.87%), above the declared 75%
  top-two threshold.
- The immutable report's `distributed_decoding_residual` label remains present
  as the original classification. The derived correction adds
  `multi_joint_output_channel_concentrated` rather than mutating history.
- The selected next hypothesis is diagnostic only: audit normalized-space
  residuals and target saturation for the two selected channels before any
  decoder, projection, normalization, threshold, or training change.
- Four focused and 81 relevant tests pass. No model load, inference,
  optimizer, checkpoint read or mutation, rollout, hardware, external compute,
  Brev, transfer, promotion, or policy acceptance occurred.
- The archive verifier now applies the same declared `1e-15` tolerance already
  used by replay metric validation. Types, keys, ordering, counts, target and
  decoded matrix hashes, signed identities, and all non-float values remain
  exact; a test rejects derived-float drift above that tolerance.

## Disposition

Accept T20.35e as a verified model-free semantic correction. Open T20.35f only
for a normalized-space residual and target-saturation audit using retained
T20.35d matrices and exact dataset statistics. Gate B remains closed; do not
select an action correction or enter Gate C.
