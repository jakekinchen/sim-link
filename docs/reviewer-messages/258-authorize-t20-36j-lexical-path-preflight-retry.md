# Reviewer Decision 258 - Authorize T20.36j Lexical-Path Preflight Retry

**Decision:** `VERIFY_LEXICAL_SNAPSHOT_CORRECTION_AUTHORIZE_PREFLIGHT_RETRY`

## Reviewed Boundary

Reviewer 257; third pre-marker failure; exact spec snapshot path and physical
offload target; correction `ad051d0529a1a484a655dbcf046bfdb030b6983d`;
origin parity; real processor smoke `5223d8f0...`; seven focused tests; 72
applicable post-install T20.36 tests; 12 pointer tests; compilation; and diff.

## Findings

- Recursive closure, offline processor construction, safe-file observation,
  network/tensor guards, batch load, and checkpoint hashing all completed. The
  failure was exact-path linkage only, before persistence or marker.
- The contract intentionally binds the lexical snapshot under
  `/Users/kelly/.cache/...`; that cache directory is physically offloaded under
  `/Volumes/cerebro/...`. Both spellings address the same snapshot but are not
  interchangeable as signed contract values.
- The correction preserves the absolute lexical input for AutoProcessor and
  evidence while resolving paths only inside the access-control guard. This
  retains exact contract linkage and resolved-blob weight denial together.
- Processor smoke `5223d8f0...` verifies under contract `cb018b69...` with the
  exact lexical snapshot, expected classes, six safe files, offline flags, and
  no network or weight/tensor access.

## Disposition

Verify correction `ad051d0` and authorize the corrected preflight retry. Its
artifacts must still be reviewed and remotely preserved before a marker.

## Withheld Authority

No attempt marker, model construction, inference, optimizer, counted attempt,
gate change, Gate C execution, hardware, external compute, or Brev.
