# Reviewer Decision 138 - Accept T17.4 Source-Bound Compiler

**Date:** 2026-07-13
**Scope:** Brief 110 / commit
`1a3746613d5856db05c901ba51e92dbdb7756c8d`

## Decision

**ACCEPT** T17.4 as verified within its declared fixture and authority scope.

## Review findings

- The compiler binds to the current T17.1 experience identity and current T17.3
  normalization identity, and independently verifies both source contracts.
- Raw action/gripper/provenance structures are retained as canonical JSON;
  unavailable values are quarantined with explicit reason codes rather than
  inferred.
- Hard-boundary and timestamp-gap logic is fail-closed. A quarantined frame
  breaks continuity and cannot be used to bridge two eligible segments.
- Deterministic Parquet/JSON output hashes, schemas, counts, and authority
  flags are verified. The current fixture correctly produces no training
  frames, no action windows, and no segments.
- The implementation commit is pushed to the required remote branch. The full
  suite's 69 import errors are environment limitations outside this slice;
  all relevant compiler/contract/pointer gates pass.

No unresolved correctness, provenance, determinism, or authority issue remains
for T17.4. T17.5 may begin only with a new brief and must preserve the empty
window result for this fixture.
