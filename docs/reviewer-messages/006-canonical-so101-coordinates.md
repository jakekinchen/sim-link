# Reviewer Decision 006 - Canonical SO-101 Coordinates

**Date:** 2026-07-10

## Decision

`CONTINUE`

## Evidence Reviewed

- One canonical module owns both coordinate directions and metadata.
- Expert, exporter, server, and evaluation launcher consume the same contract.
- Round-trip and semantic home-range tests pass in the 28-test intervention suite.
- Existing malformed data is not overwritten or reclassified as valid.

## Findings

- `100`: The known shoulder/elbow coordinate mismatch is fixed in code.
- `100`: Export artifacts can identify the transform that produced them.
- `75`: Merge validation still needs to reject old or mismatched contracts.
- `75`: Candidate normalization must not change silently during incremental training.

## Next Action

Implement T10.2, then make merge compatibility enforce both coordinate and
normalization identities before correction regeneration.
