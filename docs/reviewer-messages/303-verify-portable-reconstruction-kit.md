# Reviewer Decision 303 - Verify Portable Reconstruction Kit

**Date:** 2026-07-16  
**Support task:** K1  
**Brief:** 224  
**Decision:** ACCEPT

## Scope reviewed

Reviewed the complete portable-capsule diff, corrected canonical documentation,
the T20.42 immutable route snapshot, generated manifest, safe exporter,
templates, tests, and clean-export evidence. The active policy task remains
T20.43b; this decision grants no model, training, hardware, external-compute,
transfer, or promotion authority.

## Findings

1. **Ground truth is current.** The capsule and living guides agree on the
   verified R0 counts, terminal-negative T20.44 result, unconsumed T20.43b
   boundary, absent learned strict-v2 success, and false physical states. The
   old T20.35/T20.36 correction alphabet is retained as diagnostic history,
   not forward routing.
2. **The source boundary is reproducible.** Manifest `5067d1c2...` is rebuilt
   from portable source commit `605e4d3...`, exact Git blobs, transitive Python
   imports, package initializers, literal dependencies, and explicit globs.
   The five omissions are disjoint, hashed, reasoned, and not silently dropped.
3. **Authority does not transfer.** Live `project_state.json`, bulk outputs,
   datasets, checkpoints, private observations, external checkouts, credentials,
   and stale permits are excluded. Manifest and receipt authority/proof fields
   are false and verification compares the complete rebuilt payload, so a
   rehashed omission or changed dependency pin is rejected.
4. **Export is bounded and safe.** Destination must be new and outside the
   source repo. Paths reject absolute, parent-traversing, noncanonical, aliased,
   oversized, forbidden, or colliding entries. Failure cleanup can remove only
   the destination created by that invocation. The strict verifier rejects
   missing, changed, symlinked, or extra files.
5. **Clean-room execution is real.** Receipt `729addbb...` authenticates 336
   files and verifies before and after 31 dependency-light tests from the
   exported directory. The broader source checkout passes 153 relevant tests
   with its already pinned external runtime. External repositories remain a
   separate Stage-1 acquisition, not hidden capsule content.
6. **Historical identity drift is fixed without revisionism.** The exact
   `e9d0507` T20.41 blob is preserved as a tracked snapshot and produces the
   original signed R0 reference even though the living route file later gained
   an addendum.

## Adversarial checks

Checked authority escalation, source/selection drift, duplicate and unsafe
paths, symlinks, missing package initializers, literal fixture loss, stale live
state transplantation, non-finite JSON, omitted-file rehashing, output cleanup
scope, external checkout leakage, misleading learned/physical claims,
documentation contradictions, and unrelated dirty-path staging. No blocking
finding remains.

## Decision

Accept K1 as verified after the final manifest/state boundary is committed,
pushed to `origin/codex/pi05-autolearn-loop`, and origin equality is confirmed.
T20.43b stays the next policy task and still requires a fresh owner window plus
reviewed administrative authority epoch before any marker or model action.
