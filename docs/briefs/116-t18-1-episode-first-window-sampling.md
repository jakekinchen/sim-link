# Slice Brief 116 - T18.1 Episode-First Window Sampling

**Date:** 2026-07-13

## Objective

Create a deterministic initial sample of verified M17 windows, selected
episode-first over source class × task phase × control mode × horizon. Preserve
configured versus realized composition, source-index binding, uniqueness, and
episode/cycle accounting without opening training or mutating a data buffer.

## Contract

- Inspect only the verified T17.5b compiler/window view and the T17.7 audit.
  Verify all three source artifacts before selection; never inspect alternate
  ignored stores or normalize/reconstruct a source record.
- Partition windows by source class, one unambiguous task phase, control mode,
  and horizon. Reject a window that spans task phases, is not fully eligible, or
  cannot be traced exactly to its compiler frame/segment/source identities.
- For every realizable bucket, select one window per realized source episode
  before selecting any second window from an episode. Use a fixed explicit seed
  and domain-separated stable hash ordering. Reject bucket/episode shortfall;
  never pad, duplicate, or substitute a window.
- Record the source manifest/index hashes, configured and realized bucket/window
  counts, per-bucket episode coverage, unique-window ratio, source episode
  count, and one immutable sampling-cycle identifier. This is a selection
  manifest, not a mutable append-only buffer (T18.2 owns buffer cycles).
- Keep all model, optimizer, training, physical, raw-rewrite, external-compute,
  and Brev authority false. A sampled window is not a training authorization.

## Acceptance Criteria

- Rerun yields byte-identical selected window IDs and composition. Every bucket
  has complete episode-first coverage, and every selected ID occurs exactly once
  in the verified index.
- Tests reject source/audit/hash drift, invalid or phase-spanning windows,
  duplicate IDs, missing horizon/episode coverage, changed seed/order, short
  buckets, authority escalation, raw rewrite, and any attempt to model-load or
  modify buffer state.
- The signed manifest states exact scope limitations and is source-bound to both
  the audited replay and the T17.5b window index.

## Out Of Scope

No buffer persistence, mixture freezing, correction branching, reward/progress
changes, model loading, inference, training, optimizer, hardware, physical
motion, Brev, external compute, or deletion.

## Stop Conditions

Stop if any source view fails verification, a bucket does not contain every
realized episode, a window is phase-ambiguous, or selection would require
padding, duplication, source substitution, or changed provenance.
