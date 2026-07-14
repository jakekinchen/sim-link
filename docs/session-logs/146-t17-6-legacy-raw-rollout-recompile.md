# Executor Session 146 - T17.6 Legacy Raw-Rollout Recompile

**Date:** 2026-07-13

## Slice

Implemented T17.6 as a bounded compatibility audit of the local legacy M10
canary. The implementation does not migrate, repair, rename, or copy legacy
bytes. It records a signed candidate-by-candidate decision and emits a
source-bound zero-row compiler view only because no candidate already meets the
current T17.1 raw rollout/frame contract.

## Evidence

- The fixed inventory covers exactly three named descriptors inside the one
  configured local root: a 3,219-row observation stream, a 660-row DAgger
  sidecar, and metadata declaring 12 episodes / 11,316 frames.
- All three are quarantined. The JSONL streams lack the current signed raw
  envelope, five action variants, integer-nanosecond timing, frame provenance,
  and hard-boundary semantics; the sidecar also carries unconfined legacy image
  paths. The training metadata has a single legacy action field and legacy
  coordinate/timestamp representation.
- The signed inventory identity is
  `5ba3530040a1004fa18d641ef145fafa9e04696b6e2904ec78968439c2922826`.
  Its compiler view has 0 frames, 0 eligible frames, 0 segments, and 0 compiler
  quarantines; candidate quarantines remain in the source-bound inventory.

## Validation

- 11 focused legacy/compiler tests and the 74-test relevant regression set
  passed. The tests reject malformed rows, duplicate candidates, path escapes,
  symlink aliases, source drift, missing action/provenance/timestamp/boundary
  semantics, authority escalation, and raw rewrite attempts.
- The T17.6 writer regenerated the inventory and zero-row view byte-for-byte.
  The existing T17.4 compiler and T17.5b episode-store writers also verified
  unchanged.
- `git diff --check` and the project-state pointer guard passed. No raw legacy
  byte, hardware interface, training or optimizer, Brev resource, external
  compute service, or physical actuator was touched.

## Review Focus

The empty compiler view contains no manufactured rows: it is allowed only when
bound to the signed legacy inventory hash. The audit refuses root escapes and
all symlinks before resolving paths, preventing a named candidate from silently
redirecting to unreviewed data. `training_lock` remains closed.

## Next Suggested Slice

T17.7: build the full compiler manifest and deterministic 100-window replay
audit from the verified non-empty T17.5b source, with training still closed.
