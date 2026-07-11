# Manager Intervention 011 - Fix Measured Inertial CLI Path Safety

**Date:** 2026-07-10

## Decision

`NUDGE T16.4 CLOSEOUT`

## Evidence

Commit `522457c` passes the original nested-prior attacks. A follow-up CLI test
copied a valid canonical intake to an external temporary directory and supplied
absolute `--intake` and `--output` paths. The command raised a Python traceback
before verification or writing because `_relative_to_repo()` unconditionally
called `relative_to(REPO_ROOT)` for any absolute path.

The Python API already supports absolute temporary paths, and the CLI advertises
custom paths without stating a repo-only restriction. The synthetic proof will
also benefit from a safe bounded custom-output path.

## Resolution Required

- Preserve repo-relative paths for tracked default artifacts.
- Preserve absolute paths that are outside the repo rather than forcing them
  through `relative_to(REPO_ROOT)`.
- Ensure artifact references and file hashes remain correct for either path
  form.
- Add CLI write/verify tests using external temporary absolute intake/output
  paths, including no-overwrite behavior on invalid input.
- Then complete every synthetic-ready and negative-matrix requirement from
  brief 027.

Brief 027 is superseded by brief 028. This is an offline correctness issue; no
hardware or training authority changes.
