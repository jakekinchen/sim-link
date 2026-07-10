# Executor Session 008 - Pinned PI0.5 Normalization

**Date:** 2026-07-10

## Slice

Complete T10.2 by preventing incremental correction merges from silently changing
the accepted PI0.5 state/action normalization contract.

## Result

- Dataset aggregation now pins `meta/stats.json` from an explicit normalization
  root, defaulting to the accepted same-embodiment base dataset.
- Merge summaries record the source/output normalization hashes.
- Candidate finalization now requires both processor state files, compares their
  action/state tensors against the pinned statistics, and records all hashes.
- The cycle configuration passes the pinned stats through aggregation and finalization.

## Verification

- 18 PI0.5 autolearn tests pass.
- Accepted V10 pre/postprocessor tensors match the pinned base statistics.
- Dry-run shows the normalization arguments on aggregate and finalize stages.

## Proof Boundary

This holds action semantics stable for incremental candidates. It intentionally
does not recompute normalization from new corrections; a future migration must be
configured and evaluated as a distinct feature boundary.

## Next Step

T10.3: split selected corrections into temporally and semantically contiguous
episodes so no PI0.5 action chunk crosses a source gap.
