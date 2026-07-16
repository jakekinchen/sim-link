# Reviewer Decision 257 - Authorize T20.36j Symlink-Aware Preflight Retry

**Decision:** `VERIFY_PROCESSOR_GUARD_CORRECTION_AUTHORIZE_PREFLIGHT_RETRY`

## Reviewed Boundary

Reviewer 256; second pre-marker failure; exact Hugging Face snapshot symlink
layout; correction `54339c2cca0ff575fa2842d8bd731bec4338f87b`; origin parity;
real guarded processor smoke `3f9a4a0c...`; six focused tests; 71 applicable
post-install T20.36 tests; 12 pointer tests; compilation; and the scoped diff.

## Findings

- AutoProcessor completed with offline/local-files-only flags. The failure was
  solely the fail-closed requirement for nonempty opened-file evidence; no
  preflight, permit, or marker artifact was written.
- Hugging Face snapshot files are symlinks into a blob store. The prior guard
  compared resolved targets only to the snapshot directory and therefore
  missed safe config reads.
- The corrected guard inventories the snapshot without reading contents, maps
  each resolved target back to one or more relative names, and observes both
  lexical snapshot paths and resolved blob paths.
- The weight/tensor denial is applied after that mapping. A direct blob-store
  attempt to open `model.safetensors` fails just as its snapshot spelling does.
- Real smoke evidence records `chat_template.json`, `config.json`,
  `preprocessor_config.json`, `processor_config.json`, `tokenizer.json`, and
  `tokenizer_config.json`; it observes no network or weight/tensor access.

## Disposition

Verify correction `54339c2` and authorize the corrected preflight retry. The
resulting closure, processor smoke, corrected preflight, and one-use permit must
still be reviewed, committed, pushed, and confirmed on origin before any
attempt marker.

## Withheld Authority

No attempt marker, model construction, inference, optimizer, counted attempt,
gate change, Gate C execution, hardware, external compute, or Brev.
