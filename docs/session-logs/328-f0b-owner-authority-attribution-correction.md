# Session 328 - F0b Owner-Authority Attribution Correction

**Date:** 2026-07-17

**Task:** F0b / Brief 232

**Reviewer:** 323

## Outcome

The model-free F0b preflight caught an attribution contradiction before any
authority or renderer output existed: the overnight direction calls itself a
task-ordering source, while the initial prospective owner-grant builder cited
that path as authorization. Commit
`8edf1687168750781a257a39d9f5cace3a5e57f5` corrects the owner source to the
owner's direct eight-hour chat authorization and retains the overnight document
only as a separately named, hash-bound task-ordering source.

The canonical spec now reconstructs to `ddf71cf9...` with file SHA-256
`3513a75a...`. Fifteen focused tests pass, including explicit separation of
authorization and task-ordering fields. Compile, offline Ruff, spec rebuild,
JSON, and whitespace checks pass. HEAD, upstream, and origin all equal
`8edf168...` before this closeout.

No renderer smoke, authority artifact, checkpoint tensor read, model,
inference, optimizer, training, simulation rollout, marker, network, external
compute, Brev, hardware, or physical action occurred.

## Disposition

Reviewer 323 restores only the Reviewer-322 model-free materialization route.
A separate reviewed pre-run acceptance remains mandatory before any one-use
attempt or model action.
