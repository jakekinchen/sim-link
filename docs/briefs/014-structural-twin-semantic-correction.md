# Slice Brief 014 - Structural Twin Semantic Correction

**Date:** 2026-07-10

## Objective

Correct T16.3 so the content-addressed structural twin diff is both
reproducible and semantically trustworthy. Do not switch runtime inputs, copy
mesh assets, open hardware, or begin T16.4.

## Required Corrections

- Bind and verify the checked-in simulation-only `TwinProfile` identity as an
  explicit artifact input, alongside the dependency lock and XML hashes.
- Preserve raw XML values for provenance, but compare field-aware canonical
  values with documented tolerances.
- Normalize quaternions to unit length and one deterministic sign so equivalent
  rotations compare equal.
- Compare effective MuJoCo solver settings when `<option>` is absent rather than
  treating implicit defaults as no evidence.
- Represent any mass-bearing body whose inertia cannot be derived from the
  available source inputs as an explicit `unknown` inertial record. The
  Menagerie camera mount is the required regression case.
- Compare friction/contact properties through effective attachments, or label
  declaration-only records distinctly so unattached defaults are not presented
  as runtime behavior.
- Replace order-sensitive unnamed-geom identifiers with deterministic semantic
  identifiers where the XML provides enough attributes; otherwise surface the
  pairing limitation explicitly.
- Keep an explicit `adopt`, `adapt`, or `retain` decision for every true
  difference; no silent runtime replacement.

## Tests And Verification

- Twin-profile identity and profile-drift rejection.
- Equivalent quaternion scale/sign cases compare as matched.
- Wrist-roll and gripper-frame true deltas remain visible.
- Effective default solver comparison is emitted for both models.
- Menagerie camera-mount inertia is present as `unknown`, not silently omitted.
- Actual source-byte drift is rejected before parsing.
- A re-signed category mutation is rejected because regenerated repo state does
  not match.
- Repeated CLI write/verify is deterministic.
- Focused tests and the broader robot-lab suite pass.

## Exit Condition

A fresh reviewer accepts the corrected artifact and its proof. Only then may the
ledger advance to a fail-closed T16.4 measured-mass intake compiler.
