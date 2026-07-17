# Reviewer Decision 312 - Accept RGB Camera Runtime Timeout Correction

**Date:** 2026-07-16

## Decision

`ACCEPT_60_SECOND_FORMAL_DOCTOR_TIMEOUT_AND_REBIND_K3_GATE`

Origin commit `e6db0b95cb43b3066da449f92610731e395c8763` changes only the
formal `codex doctor` subprocess ceiling from 30 to 60 seconds, asserts that
bound in the existing runtime-profile tests, and includes the profile source
and test in K3's scoped origin-clean check. The exact doctor command completed
in 33.51 seconds with a valid JSON report; the previous attempt wrote no
authority artifacts and performed no hardware enumeration or open.

Both pinned robot runtimes pass 25 profile-plus-camera tests. The correction
does not relax active-thread identity, `danger-full-access`, approval `never`,
maximum profile age, central composition, one-use permit, RGB-only scope, or
any depth/serial/motion prohibition. Rebind the still-unused K3 gate to
`e6db0b9...` and continue with one fresh preflight.
