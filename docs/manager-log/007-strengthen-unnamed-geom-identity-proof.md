# Manager Intervention 007 - Strengthen Unnamed Geom Identity Proof

**Date:** 2026-07-10

## Decision

`REDIRECT THEN CONTINUE`

## Evidence

The current fallback identifier is derived from the raw sibling index, for
example `wrist[1]`. Rebuilding the same unchanged XML is deterministic, so a
repeat-generation test alone cannot prove the defect is fixed. Inserting or
reordering an unrelated visual geom changes those identifiers and can pair a
runtime mesh with a Menagerie primitive merely because they occupy the same
position.

## Resolution Required

The closing T16.3 slice must prove invariance under harmless sibling reordering,
not just repeated parsing. Unnamed collision records need a canonical semantic
identity or deterministic multiset grouping derived from normalized structural
attributes. If two sources have no defensible correspondence, report
missing/extra records instead of manufacturing a mismatch by ordinal position.

Brief 019 is superseded by Brief 020. T16.3 stays `in_progress` until this
stronger proof passes.
