# Reviewer Decision 256 - Authorize T20.36j Corrected Preflight Retry

**Decision:** `VERIFY_METADATA_CORRECTION_AUTHORIZE_UNCOUNTED_PREFLIGHT_RETRY`

## Reviewed Boundary

Owner grant; Reviewer 255; exact offline install output; pre-marker failure;
wheel METADATA and editable PKG-INFO bytes; correction
`9e9272c5a9dca584b69db5963036c22b37668f26`; origin parity; live 57-package
closure `ac8abed1...`; 70 applicable post-install T20.36 tests; 12 pointer
tests; central-authority verifier; compilation; and the scoped diff.

## Findings

- The failure occurred during recursive metadata collection, before
  AutoProcessor, model construction, permit, marker, inference, or optimizer.
- LeRobot is visible as both `dist-info/METADATA` and editable
  `egg-info/PKG-INFO`. The two 28,475-byte files are byte-identical with
  SHA-256 `ceb9917f...`; accepting the standard editable filename does not relax
  dependency semantics.
- Duplicate names remain fail-closed unless version, raw metadata hash, and
  `Requires-Dist` rows match exactly. Conflicting aliases cannot be hidden.
- The corrected live closure signs 57 active packages, exact authorized
  versions, and no missing or mismatched requirement.
- The two historical tests omitted post-install are intentionally tied to the
  prior missing-package environment; their checked-in signed audit artifacts
  and verification history are unchanged.

## Disposition

Verify correction `9e9272c` and authorize one retry of the still-uncounted
corrected preflight. It may construct AutoProcessor under the existing offline
and tensor-read guards. Any resulting closure, processor, preflight, and permit
artifacts remain non-executable until reviewed and remotely preserved.

## Withheld Authority

No attempt marker, model construction, training, second replacement attempt,
retry/sweep of the counted attempt, gate change, Gate C execution, hardware,
external compute, or Brev.
