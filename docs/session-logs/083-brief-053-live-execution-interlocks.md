# Session 083 - Brief 053 Live-Execution Interlocks

**Date:** 2026-07-11

Brief 053 began offline at `2026-07-11T14:24:03-05:00` from remotely matched
HEAD `1bbd539`; start boundary `150cd58` recorded the exact no-hardware scope.
Implementation `d76baf5` is present on `origin/codex/pi05-autolearn-loop`. The
live gate and training lock remained closed.

The committed Codex project default changes from unattended broad access to
`workspace-write` plus `on-request`. Separate hardware-supervised and
offline-autonomous fragments encode `danger-full-access`/`on-request` and
`danger-full-access`/`never`, respectively. The hardware runtime artifact does
not trust those files alone: it runs an exact explicitly configured `codex
doctor`, hashes the report, and cross-checks the latest persisted `turn_context`
for the active `CODEX_THREAD_ID` before and after capture. It binds the turn,
thread, repository, executable/version, approval and sandbox policies, profile
files, and a five-minute freshness limit. Stale, synthetic, cross-thread,
re-signed, aliased, parent/child-mismatched, or mid-capture policy changes fail.

That distinction found and corrected a real review flaw during implementation:
a child doctor process initially reported the newly loaded project config rather
than the active parent's policy. The final verifier reads the active rollout
context too. The current parent remains `danger-full-access`/`never`, so it is
mechanically live-ineligible even though the future hardware profile is
`on-request`.

The production factory boundary reverifies the full live candidate contract and
the active same-thread hardware profile before exposing any constructor. Its
one-shot Feetech path rechecks the pinned LeRobot sources, protocol 0, 1 Mbps,
six STS3215 identities, exact canonical/TTY follower paths, raw
`Present_Position`, `handshake=false`, zero retries, and
`disable_torque=false`. The camera path pins FFmpeg 8.0.1 at the exact resolved
path and SHA-256 `0a96da27...`, rehashes the fresh stable/capture identities and
signed mode, and consumes each named finite camera once. Tests replace the raw
bus and camera constructor; no production constructor ran.

Candidate result schema v2 binds the hardware-profile identity. Fixed private
success and failure schemas embed the candidate contract and profile, retain no
proof label, and conservatively classify failures. The writer allows exactly one
exclusive content-addressed artifact per session and independently rehashes its
reference; session reuse, existing files, symlinks, path escape, class drift,
contract/profile/result substitution, and content mutation reject.

Ninety focused tests pass in both `.mujoco_venv` and the pinned LeLab runtime.
Both source verifiers agree on profile, Feetech, and FFmpeg identities.
Compilation, duplicate literal-dictionary detection, source-safety, JSON/TOML,
and diff checks pass. The 289-test offline authority/twin gate passes in 73.993
seconds. A real active-runtime negative check rejects this parent before the
doctor subprocess can run.

No hardware was enumerated, instantiated, or opened. No serial/camera/Studio
access, reconnect, register write, torque transition, motion, policy
preprocessing/inference, MuJoCo replay, optimizer, paid compute, destructive
action, or unrelated path was touched. Grant only the three local conformance
capabilities recorded in canonical state. A separate offline production-session
orchestrator remains required before any new hardware-supervised thread may
request a reviewed live-gate transition.
