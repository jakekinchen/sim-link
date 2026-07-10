# Reviewer Decision 008 - Contiguous Correction Episodes

**Date:** 2026-07-10

## Decision

`CONTINUE`

## Findings

- `100`: A LeRobot episode can no longer span a selected-frame time gap.
- `100`: Sidecars preserve source episode and segment identities.
- `75`: Corrections still need the actual prompt used by the policy.

## Next Action

Implement T10.4 frame-level policy-task persistence and export.
