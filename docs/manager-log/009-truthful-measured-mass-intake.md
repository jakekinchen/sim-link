# Manager Intervention 009 - Truthful Measured Mass Intake

**Date:** 2026-07-10

## Decision

`REDIRECT T16.4 THEN CONTINUE`

## Evidence

Brief 023 requires a current-arm artifact with measured-part inputs and compiled
aggregate mass, COM, and inertia, but no genuine physical SO-101 weight evidence
exists in the repository or its history. The TwinProfile keeps
`full_arm_mass_kg` unknown. The seven explicit runtime/Menagerie masses
(`0.147`, `0.100006`, `0.103`, `0.104`, `0.079`, `0.087`, and `0.012` kg;
`0.632006` kg total) are CAD/MJCF priors, not measurements of this printed arm.

Executing brief 023 literally would either stop immediately under its own
missing-evidence rule or create a misleading physical result.

## Resolution Required

T16.4 completes the offline intake and compilation capability without claiming
that the current arm has been measured:

- Check in an immutable real intake with status `awaiting_measurements` and no
  fabricated measurements.
- Check in a deterministic real result with status
  `blocked_missing_measurements`, null aggregate physical outputs, explicit
  missing coverage, and no qualification/training authority.
- Prove the ready aggregation path with a clearly `synthetic_test_only` fixture.
- Keep CAD geometry/inertia priors separate from evidence whose origin is
  `measured`; CAD priors may shape/scale inertia only after trusted measured mass
  exists.
- Reject overlapping parent/child coverage, duplicate evidence, ambiguous
  assembly/frame assignment, stale/tampered bindings, and invalid inertias.
- A normal write/verify must reproduce truthful blocked state; an explicit
  `--require-ready` check must fail nonzero until real measurements arrive.

Brief 023 is superseded by brief 024. Physical qualification and all training
remain closed.
