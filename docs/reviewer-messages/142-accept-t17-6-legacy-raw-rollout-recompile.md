# Reviewer Decision 142 - T17.6 Legacy Raw-Rollout Recompile

**Date:** 2026-07-13

## Decision

`CONTINUE`

## Evidence Reviewed

- Brief 114; implementation commits `520ca0c` and `68b20ed`; the signed
  legacy inventory; the explicit zero-row compiler view; and Session 146.
- 11 focused legacy/compiler tests, the 74-test relevant regression set,
  byte-identical T17.6 writer verification, and unchanged T17.4/T17.5b writer
  verification.

## Findings

- The audit is intentionally bounded to three named M10 descriptors. It does
  not scan other ignored outputs, user directories, external checkouts, network
  sources, or hardware.
- The 3,219-row observation stream and 660-row intervention sidecar are not
  current signed raw-rollout/frame evidence. Their action lineage, timing,
  source/frame provenance, and hard-boundary semantics cannot be inferred.
  The 12-episode training metadata is a legacy training representation, not a
  raw source record. Quarantine is therefore correct.
- The zero-row compiler view is not synthetic data: empty compilation is
  permitted only with the signed legacy-inventory hash, and no placeholder
  frame, segment, action, or transition is generated. Root escapes, duplicate
  candidates, and both external and in-root symlink aliases fail closed.
- No training, optimizer, raw rewrite, hardware, physical actuation, external
  compute, or Brev authority was gained. The central training lock remains
  closed.

## Routing

T17.6 is verified with zero accepted legacy records. T17.7 is the next pending
offline task and must audit the verified non-empty T17.5b source rather than
reopening migration of these quarantined records.

## Manager / Human Escalation

None. This compatibility result does not authorize training, physical work, or
external compute.
