# Session 081 - Brief 051 Stable Camera Identity

**Date:** 2026-07-11

Brief 051 began from remotely matched HEAD `2a42591` at
`2026-07-11T13:24:36-05:00`. Start boundary `8a437d5` quarantined future live
source binding after review found that the accepted v4 manifest's camera digest
included the capture-time numeric AVFoundation index. The live gate and training
lock remained closed.

Implementation `bff160d` advances the redacted manifest to v5. It retains the
complete capture-selection digest for attempt audit and adds a second digest
over exact camera name, unique ID, model ID, and signed input mode, excluding
only the numeric index. Historical v4 evidence remains independently verifiable
but exposes no stable-binding capability and cannot satisfy the exact v5 pin
used by downstream artifacts.

The migration rehashed the immutable attempt-006 private evidence and all four
private frame files before producing manifest `5218c3bd...`. The private
evidence identity remains `125de28f...`. Stable camera identities are
`69d55167...` and `9931d030...`; the original full capture identities remain
present separately. CalibrationProfile `24db6f24...`, static-pose contract
`7260be3e...`, fixture observation `9ad35d18...`, and fixture result
`6b40e275...` were regenerated from the new exact source chain. Static contract,
observation, result, and runtime-result schemas advance to v2 so the old generic
camera field cannot be consumed accidentally.

Sixty-seven focused tests pass in both `.mujoco_venv` and the pinned LeLab
runtime. The manifest/private-bundle, calibration, static-pose, and read-only
source verifiers pass. Compilation, JSON, privacy, and diff checks pass. The
266-test authority/twin gate passes in 79.568 seconds.

Same-agent review verified that numeric index churn alone preserves the stable
digest; name, unique-ID, model-ID, or input-mode changes do not. Re-signed
capture/stable substitutions reject, duplicate stable identities reject, v4
downgrade cannot satisfy v5 consumers, private references are content-rehashed,
and migration paths are canonical and basename-safe. No raw camera, USB, or
device identity entered the tracked artifacts.

No hardware was enumerated or opened. No Studio call, reconnect, register
write, torque change, motion, policy preprocessing/inference, MuJoCo replay,
optimizer, paid compute, destructive action, or unrelated path was touched.
Grant only `stable_camera_identity_binding_valid` while preserving prior local
fixture capabilities. A separate offline live-candidate runner and another
review remain mandatory before any live-gate transition.
