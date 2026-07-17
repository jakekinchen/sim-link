# Reviewer Decision 309 - Verify T20.43c Model-Free Materialization Recovery

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43C_MODEL_FREE_MATERIALIZATION_RECOVERY`

The interrupted administrative materialization may resume from its exact
completed renderer-smoke output after this correction is committed and exact on
origin. Training remains locked.

## Interruption boundary

At `2026-07-16T22:05:02-05:00`, the actual T20.43b-schema mirror smoke
completed and emitted MP4 SHA `955ad918...` plus manifest identity
`00494310...`. The subsequent parent-process dependency inventory imported an
obsolete Python-3.11 MuJoCo site-packages path under the Python-3.12 runner and
failed before writing any authority artifact. No owner grant, central request,
decision, runtime preflight, permit, acceptance, continuation marker,
checkpoint tensor read, model, optimizer, inference, rollout, or Gate C action
occurred.

## Corrective review

- The materializer now inserts the already-bound Python-3.12 MuJoCo support
  path for its dependency inventory instead of depending on caller path order.
- A resume is allowed only when the smoke receipt is absent and both expected
  smoke outputs already exist. The MP4, signed manifest, source-trace linkage,
  v2/legacy renderer hashes, sizes, and identities are reconstructed before
  reuse.
- The signed smoke receipt records
  `resumed_after_post_render_materialization_failure: true`; the completed
  smoke bytes are not rewritten.
- Reviewer 308's empty/partial-run terminal preservation and symlink rejection
  remain intact.

Seven focused tests and the selected T20.43/T20.43b/T20.43c/T20.44 plus
central-composer set pass: `58 passed, 15 subtests passed`; Reviewer 308's
broader 70-test hardening receipt remains separately preserved. Compilation and
whitespace checks pass. Fresh adversarial review found no evidence spoofing,
retry authority, path alias, source-tree mutation, model action,
hardware/network/external/Brev grant, or destructive operation.

## Disposition

Only the still-unconsumed model-free authority materialization may resume after
this reviewed correction is exact on origin. A later authority review and
signed acceptance remain mandatory before any marker.
