# Reviewer Decision 308 - Verify T20.43c Terminal Preservation Hardening

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43C_TERMINAL_PRESERVATION_HARDENING_MODEL_FREE`

The T20.43c implementation remains accepted for future model-free authority
materialization. No continuation marker or model action is accepted here.

## Review finding and correction

Reviewer 307 established the intended immutable continuation boundary, but a
fresh adversarial pass found one narrow post-marker evidence gap: the inherited
tree helper rejects an empty directory. If infrastructure failed after the
one-use marker but before `progress.json` was written, failure signing could
raise while trying to hash the still-empty run root.

The runner now uses a T20.43c-specific partial-tree helper that:

- returns an empty signed tree when the run root is absent or contains no files;
- hashes every available partial file once output exists; and
- continues to reject a symlink at the root or anywhere below it.

Both live failure verification and exception-path failure creation use the
same helper, so an empty-tree terminal receipt reconstructs deterministically.

## Verification

- Seven focused T20.43c tests pass, including absent, empty, populated, and
  symlinked partial-tree cases.
- Seventy selected T20.43/T20.43b/T20.43c/T20.44, authority-composer, and
  project-pointer regressions pass.
- Ruff lint and format checks pass for all seven T20.43c implementation files.
- No authority artifact, checkpoint tensor read, model construction/load,
  inference, optimizer, rollout, Gate C, hardware, network, external compute,
  or Brev action occurred.

## Disposition

After this exact implementation is committed and preserved on origin, only
the already bounded actual-schema smoke and compact model-free authority
materialization may proceed. The newer explicit owner proceed instruction,
recorded in Brief 227's owner addendum, supersedes the earlier scheduling-only
prohibition. The training lock remains closed until separate authority review
and acceptance.
