# Session 077 - Brief 048 Signed Calibration Profile

**Date:** 2026-07-11

The session resumed from remotely preserved Brief 048 start `dd2f770`, with
T16.5b accepted and both the live gate and training lock closed. The persisted
Goal backend still reported its historical blocked state; the owner's explicit
resume is recorded in canonical state, while replacement was rejected because
the runtime exposes no resume transition. No goal state was falsified.

Implementation `700be05` adds a strict offline CalibrationProfile builder,
verifier, writer, tracked artifact, and adversarial tests. Profile
`b360b4f6...` binds calibration `192404b6...`/770 bytes, accepted live manifest
`eff3c824...`/file `cd4120f0...`, and servo identity digest `66e9d363...`.
Exactly six names and IDs, unique identity, integer decoded STS3215 homing
offsets, raw ranges, drive mode zero, live models/firmware, body-degree
normalization, and gripper 0=closed/100=open semantics are required.

Verification passed:

- 6 focused tests covering identity, numeric/domain, source-substitution,
  semantic-tamper, privacy, and authority-escalation failures;
- independent checked-in artifact rebuild via
  `write_calibration_profile.py --verify`;
- `py_compile` and `git diff --check`;
- 238 authority/twin regression tests in 87.588 seconds.

Same-agent adversarial review found no global-authority grant, raw device path,
USB serial, non-finite acceptance, source alias, nondeterministic ordering, or
hardware side effect. Two unused local symbols were removed and the focused
gate rerun. The implementation commit was pushed and local, upstream, and
origin all resolved to `700be05468c15e3660bf481931f77e49af49d527`.

Brief 048 grants only `calibration_profile_semantically_valid`. T16.5c remains
in progress: static-pose bracketing, coordinate validation, policy-ready input,
PI0.5 preprocessing/shadow, and matched MuJoCo replay are not yet proven. No
serial port, camera, Studio endpoint, reconnect, write, torque transition,
motion, policy inference, optimizer, paid compute, or destructive action was
used. T16.6 remains pending and no motion was attempted.
