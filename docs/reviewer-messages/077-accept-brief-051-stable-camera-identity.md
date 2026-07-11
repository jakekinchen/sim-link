# Reviewer Decision 077 - Accept Brief 051 Stable Camera Identity

**Date:** 2026-07-11

## Decision

`CONTINUE T16.5C; ACCEPT STABLE CAMERA IDENTITY; LIVE GATE CLOSED`

Implementation `bff160d77003d4675f015fdaec1d9d839f3d9982` is present on
`origin/codex/pi05-autolearn-loop`. Manifest v5 `5218c3bd...` independently
rebuilds from unchanged private evidence `125de28f...` and its four
content-addressed frame files. It preserves complete capture-selection hashes
for audit and exposes separate stable hashes over exact name, unique ID, model
ID, and input mode while excluding only the volatile numeric index.

The exact v5 manifest is pinned through CalibrationProfile `24db6f24...` into
static-pose contract `7260be3e...`; fixture observation/result identities are
`9ad35d18...` and `6b40e275...`. Static bracket and runtime schemas advance to
v2 and consume only `stable_camera_identity_sha256`.

Adversarial tests prove numeric index churn preserves the stable digest while
name, unique-ID, model-ID, and mode changes do not. Implementation and review
also fail closed on re-signed digest drift, malformed or duplicate stable
identities, source substitution, path escape, and private-file identity drift.
Legacy v4 verification is retained only for historical evidence and cannot
satisfy the pinned v5 calibration/static-pose chain.

Sixty-seven focused tests pass in both pinned runtimes; four offline verifiers,
compilation, privacy, JSON, and diff checks pass; and 266 broad tests pass. No
hardware or policy path ran.

Grant only `stable_camera_identity_binding_valid` and preserve the prior local
calibration/fixture capabilities. This is not a live permit, live bracket,
synchronized or policy-input-valid observation, shadow, physical qualification
or transfer, motion, promotion, or training authority. Next implement the
source-bound live-candidate contract/runner offline, then review it separately
before considering a live-gate transition.
