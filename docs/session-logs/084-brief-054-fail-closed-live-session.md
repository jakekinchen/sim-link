# Session 084 - Brief 054 Fail-Closed Live Session

**Date:** 2026-07-11

Brief 054 began offline at `2026-07-11T15:05:42-05:00` from remotely matched
HEAD `28d0931`. Implementation
`ce7a794bb36de16c6a053608771cd5ecbd87575a` is present on
`origin/codex/pi05-autolearn-loop`. The live gate and training lock remained
closed.

The new production entry point completes every non-hardware preflight before
the session-start boundary: it verifies the active same-thread hardware profile,
the complete candidate contract, an existing non-aliased private root with an
unused immutable session identity, and the exact pinned one-shot transport and
two-camera factory specifications. A preflight rejection cannot invoke the
candidate runner or write a session artifact.

After session start, candidate or cleanup failure builds, verifies, exclusively
writes, and independently rereads one private failure artifact before raising a
typed rejection with no candidate result. Candidate success does not return
until the private success artifact has passed the same one-write/reverification
boundary and a signed session receipt verifies. The receipt binds the candidate
contract, active-profile identity, result, private evidence, canonical private-
reference digest, and private-root identity. It is candidate-only, carries no
proof label, and grants no motion, policy, transfer, promotion, or training
authority.

Same-agent adversarial review found two gaps before acceptance. First, an
exception from the post-run wall-clock source could replace a candidate failure
or leave a successful candidate without a durable rejected outcome. The final
path preserves both failures when present, uses the trusted start time only for
the rejection record, and never returns the result. Second, a missing, reused,
or ancestor-aliased private destination could have been discovered only after
the runner began. It is now rejected during preflight and checked again at the
exclusive write boundary; grandparent aliases are covered.

One hundred one focused tests pass in both `.mujoco_venv` and the pinned LeLab
runtime. Execution, candidate, camera-identity, calibration, and static-pose
artifact/source verifiers all pass. Compilation, duplicate literal-dictionary,
and diff checks pass. The 300-test offline authority/twin gate passes in 92.360
seconds. A real active-runtime negative check still rejects this parent with
`Active Codex thread is not using on-request approval` before a doctor
subprocess can execute.

Every production constructor and candidate runner was patched in tests. No
hardware was enumerated, instantiated, or opened. No serial, camera, Studio,
reconnect, register-write, torque, motion, policy, MuJoCo, optimizer, training,
paid-compute, destructive, or unrelated-dirty-path action occurred. Grant only
`fail_closed_static_pose_live_session_orchestrator_conformant`. A separate
offline redacted candidate-session review manifest remains next; no live-gate
transition is authorized in this thread.
