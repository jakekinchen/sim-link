# Session 082 - Brief 052 Source-Bound Live Candidate

**Date:** 2026-07-11

Brief 052 began offline at `2026-07-11T13:44:45-05:00` from remotely matched
HEAD `a959fa3`; start boundary `db8d3c7` recorded the exact candidate-only scope.
The live gate and training lock remained closed.

Implementation `79eee89` adds exact contract/result schemas and fixed,
separate production-live and deterministic-fixture builders, runners, and
verifiers. The contract binds the complete canonical project-state snapshot and
digest, an open unconsumed one-session gate, active owner-presence lease, exact
accepted discovery, follower USB and all signed aliases, stable camera
identities with fresh numeric-index resolution, pinned manifest/calibration/
static sources, finite duration, exact operation counts, and the no-write
lifecycle. Production execution emits candidate-only evidence with no physical
proof label.

The shared bracket runtime now produces an unclassified lifecycle capture before
the fixed caller assigns an evidence class. Exact transport/camera mode pairs
distinguish deterministic fixture, source-bound candidate fixture, and injected
live execution. Fixture execution records `hardware_opened=false`; changing and
re-signing the evidence class cannot convert it into live evidence. Follow-up
commit `2c0b903` explicitly binds the fixture camera evidence mode in the
existing runtime regression.

The accepted private discovery resolver independently verifies discovery
`b57fbec8...`, follower USB identity `c5bd66ff...`, stable camera identities
`69d55167...` and `9931d030...`, and numeric-index churn from `[0, 1]` to
`[10, 21]` without enumerating hardware. Seventy-seven focused tests pass in
both `.mujoco_venv` and the pinned LeLab runtime. The source resolver passes in
both runtimes; manifest migration, calibration, static-pose, read-only source,
compilation, JSON, privacy, safety-source, and diff checks pass. The 276-test
authority/twin regression gate passes in 72.567 seconds.

Same-agent review verified fail-closed handling for stale, expired, consumed,
wrong-scope, wrong-session, or re-signed gate/lease/state evidence; follower
USB, alias, holder, camera identity/index/mode, source, timing, operation-count,
pose, lifecycle, and authority drift; unexpected writes, torque changes, or
motion; and construction, primary, release, close, and post-holder failures.

No hardware was enumerated or opened. No serial/camera/Studio call, reconnect,
register write, torque transition, motion, policy preprocessing/inference,
MuJoCo replay, optimizer, paid compute, destructive action, or unrelated path
was touched. Grant only `static_pose_live_candidate_contract_valid` and
`source_bound_static_pose_live_candidate_runtime_conformant`. The live gate
cannot be reconsidered until exact pinned hardware factories, immutable private
success/failure evidence, and a machine-checked hardware-supervised on-request
profile are verified offline, followed by a fresh finite run window and a
separate reviewed remote gate transition.
