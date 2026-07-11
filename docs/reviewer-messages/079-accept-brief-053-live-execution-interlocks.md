# Reviewer Decision 079 - Accept Brief 053 Live-Execution Interlocks

**Date:** 2026-07-11

## Decision

`CONTINUE T16.5C; ACCEPT BRIEF 053 LIVE-EXECUTION INTERLOCKS; LIVE GATE CLOSED`

Implementation `d76baf579739c919420aa94b54507f0e42aafc5e` is present on
`origin/codex/pi05-autolearn-loop`.

The project no longer commits unattended broad access as its default. The
default is `workspace-write`/`on-request`, while exact separate hardware and
offline fragments encode `danger-full-access`/`on-request` and
`danger-full-access`/`never`. More importantly, the hardware-profile verifier
does not infer the active parent's policy from those files. It binds an explicit
doctor report to the latest persisted same-thread `turn_context`, checks both
before and after capture, and rejects stale, cross-thread, synthetic, re-signed,
aliased, parent/child-mismatched, or mid-capture drift.

This corrects a material issue found during same-agent review: a new child
process can report a newly edited on-request config while the running parent is
still `never`. The final implementation detects that exact condition. The
current thread is mechanically live-ineligible and cannot authorize a hardware
factory or live runner.

Both production factory paths reverify the full candidate contract and active
profile before any constructor is exposed. The transport is one-shot and binds
the code-pinned Feetech implementation, six exact motors, protocol 0, 1 Mbps,
canonical plus TTY follower identity, no-handshake raw position reads, and
no-torque close. The two one-use cameras bind fresh stable and capture hashes,
exact signed modes/frame counts, and FFmpeg 8.0.1 at SHA-256 `0a96da27...`.

Candidate result v2 binds the hardware-profile identity. Private success and
failure v1 artifacts have fixed classes, embed the contract/profile, grant no
proof label, and can be written only once per session through an exclusive
content-addressed path. Re-signing, substitution, symlink, escape, session
reuse, and content-drift cases fail.

Ninety focused tests pass in each pinned runtime; both source verifiers,
compilation, source-safety and diff checks pass; and 289 broad tests pass in
73.993 seconds. All hardware constructors and subprocesses were injected fakes.
No hardware or policy path ran.

Grant only `pinned_static_pose_live_factory_spec_conformant`,
`private_static_pose_live_candidate_evidence_conformant`, and
`hardware_supervised_runtime_profile_validator_conformant`. Do not grant a live
candidate result, static-pose observation, policy-input validity, shadow,
actuation, physical qualification/transfer, promotion, or training authority.

Next implement one fail-closed offline production-session orchestrator that
persists exactly one private success or failure artifact. Any later live-gate
transition requires a new parent thread whose persisted active policy is
hardware-supervised/on-request, a fresh finite window, separate reviewed remote
gate commit, fresh presence lease, and fresh discovery/all-alias zero-holder
evidence. The current live gate and training lock remain closed.
