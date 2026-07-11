# Session 078 - Overnight Authority And Twin Closeout

**Date:** 2026-07-11

## Final state

- Branch: `codex/pi05-autolearn-loop`.
- Pre-closeout HEAD: `7100c1cf75f4f50771140893a0eefb1ba8e687e6`;
  derive the commit containing this log at runtime.
- Run: start `02:14:07 CDT`; no-new-major-slice cutoff `11:44:07 CDT`;
  closeout recorded `11:44:39 CDT`; hard deadline `12:14:07 CDT`.
- Verified: T16.2b-A, T16.4b on fixture evidence, T16.2b on fixture evidence,
  T16.5a, and T16.5b.
- In progress: T16.5c, with Brief 048 verified.
- Pending: T16.6 and all later physical qualification/training work.
- Locks: `live_gate=closed`, `training_lock=closed`.

## Remote-preserved commits

Every commit created after launch base `5901439` was pushed to
`origin/codex/pi05-autolearn-loop`. Ordered history through the pre-closeout
HEAD contains 61 commits:

```text
c0b9629 feat(robot-lab): centralize authority composition
e1d59ca docs: review central authority composition
0d67b8f docs: verify authority composer boundary
9b660ff docs: record supervised hardware authority
a93ff05 feat(robot-lab): add production inertial compiler
bc5d4fe docs: review production inertial compiler
e70586e docs: open inertial numerical hardening
7d05629 fix: harden inertial eigensolver numerics
dbdd1ef docs: review T16.4b numerical hardening
785c002 docs: close T16.4b and open T16.2b
710960b feat: compute twin qualification from evidence
383557b docs: review computed twin qualification
a889fa8 docs: close T16.2b and open offline census
f200087 feat(robot-lab): add offline no-write census preflight
d002c80 docs: review offline no-write census
e14fc50 docs: close offline census and open live preflight
3963225 docs: reopen census protocol binding
5102422 fix(robot-lab): bind census to Feetech protocol zero
eeb16e1 fix(robot-lab): derive census constants from source binding
2407299 docs: review corrected census protocol binding
b1a7702 docs: reclose corrected census and reopen live preflight
16d24ea feat(robot-lab): add bounded live read-only observation harness
0dc0ed1 docs(robot-lab): review T16.5b offline live harness
b85a253 fix(robot-lab): allow absent USB manufacturer label
e351f69 docs(robot-lab): review T16.5b metadata discovery
2018b6d docs(robot-lab): reject unstable T16.5b live attempt
ea99ec9 fix(robot-lab): bind finite camera capture by stable identity
66003d8 fix(robot-lab): validate finite PNG pixel stream
fd13bf6 test(robot-lab): trace named camera audits into evidence
01802a0 fix(robot-lab): block concurrent serial device holders
c686ab6 docs(robot-lab): review stable camera and serial gates
eaeaa52 docs(robot-lab): record serial holder owner gate
c06188b docs(robot-lab): escalate Studio disconnect authority
ee2ccfe docs(robot-lab): block T16.5b on owner authority
59f09d1 docs(robot-lab): authorize virtual follower disconnect
b211562 docs(robot-lab): verify virtual follower disconnect
2da4817 docs(robot-lab): open bounded read-only live gate
376a9c5 docs(robot-lab): reject second live camera attempt
2d1cd97 fix(robot-lab): retain bounded camera failure diagnostics
07cd453 docs(robot-lab): require state-integrity live gates
7ea2665 feat(robot-lab): bind disconnect and alias safety proofs
3710842 docs(robot-lab): close Brief 043 state gates
37fced9 docs(robot-lab): open one finite live session
169defe docs(robot-lab): reject live framerate attempt
4ae0521 fix(robot-lab): bind supported camera framerate
cee8240 docs(robot-lab): close Brief 044 camera mode
26a2824 docs(robot-lab): open one v2 live session
9927da2 docs(robot-lab): reject live pixel-format attempt
820a40f fix(robot-lab): bind per-camera input modes
a6da4b4 docs(robot-lab): close Brief 045 camera modes
09fc358 docs(robot-lab): open one exact-mode session
ca86f7c docs(robot-lab): reject output-dimension drift
6eb5f89 fix(robot-lab): reject camera dimension drift
9631169 docs(robot-lab): close Brief 046 dimensions
e68068a fix(robot-lab): require policy-useful camera modes
4b8d1d5 docs(robot-lab): close Brief 047 camera floor
68e11b9 docs(robot-lab): open final exact-mode session
159e001 feat(robot-lab): accept finite live observation
dd2f770 docs(robot-lab): open calibration profile slice
700be05 robot-lab: add signed calibration profile
7100c1c docs: close Brief 048 calibration profile
```

## Verification and artifact identities

- Central authority contract `6d04b205...`; denied composition `d1206c5c...`;
  local assembly inertials `8b8aab8e...`. The composer grants no global state.
- Production inertial fixture input `fe9dbd54...`, output `b8d7c5d2...`, and
  fixture denial composition `72eb3f40...`; 17 focused and 131 broad tests.
- Computed qualification spec `eff5a15e...`, fixture report `7ed02c6e...`, and
  denial composition `41a4d731...`; 16 focused and 147 broad tests.
- Offline census contract `73652ffa...`, trace `17921a5f...`, result
  `4a83298b...`; 16 focused and 195 broad tests.
- Accepted live manifest `eff3c824...`/file `cd4120f0...`; private evidence
  `125de28f...`; 54 reads, six `Torque_Enable=0`, four exact 640x480 PNGs,
  zero writes/torque changes/motion, zero alias holders, complete cleanup.
- CalibrationProfile `b360b4f6...`, calibration `192404b6...`, servo identity
  `66e9d363...`; 6 focused tests, independent verifier, compilation, and 238
  broad authority/twin tests in 87.588 seconds. A final 24-test state/profile/
  composer gate and workflow audit also passed.

## Bounded live operations and proof state

One owner-authorized Studio POST disconnected only the follower at
`08:57:17 CDT`; HTTP 200, call count 1, no retry, permit consumed, leader still
connected, follower torque reported off, safety/routing unchanged, zero running
jobs, zero holder, and no motion. Live attempts 001-005 were rejected without
accepted labels; their failures drove identity, holder, framerate, pixel-format,
and output-dimension corrections. Attempt 006 alone was accepted and grants
only `live_read_only_census_observed` and `physical_observation_capture`.

No physical motion command, general register/configuration write, policy
actuation, reconnect, or T16.6 permit was executed. The sequential capture is
not synchronized, policy-input-valid, physical qualification, transfer
readiness, or autonomous-policy success. The follower remained virtually
disconnected with torque reported off at the last accepted evidence boundary.

## Remaining work and risks

Next, write an offline brief that defines parsed-profile coordinate validation
and a fast `q_before -> finite camera batch -> q_after` static-pose bracket with
a signed tolerance and complete cleanup. Only after separate implementation,
tests, review, commit, push, and remote confirmation may a fresh owner-presence
lease reopen a finite read-only gate. Then prove actual PI0.5 preprocessing,
model-ready tensor hashes, shadow actions only, semantic/range audit, and matched
MuJoCo replay without transmission.

T16.6 remains blocked by incomplete T16.5c, current-pose/limit/config telemetry,
watchdog/deadman/stop/shutdown proofs, and an exact signed session permit. Do not
rush motion. Broader configuration census, generated status views, supervised
versus offline Codex profiles, remote CI, and post-proof module decomposition
remain follow-up work. The persisted Goal backend still exposes the historical
`blocked` state and no resume transition; owner resume authority is durable in
canonical state, and the old goal was neither falsely completed nor replaced.

No subagent, optimizer training, Brev or other paid compute, merge, rebase,
force-push, pull request, destructive operation, or unrelated-path staging was
used. Brev was not started. Unrelated pre-existing dirty and untracked paths
remain preserved exactly outside the scoped commits.
