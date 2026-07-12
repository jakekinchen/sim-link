# Session 092 - Resumed Session-Metadata Profile Correction

**Date:** 2026-07-12

The first real static-pose preflight failed before discovery because the active
rollout contained three `session_meta` records after desktop/app-server resume.
The records preserve the same thread, cwd, originator, CLI version, source,
model provider, timestamp, git source, and all other existing fields; the later
records only add `memory_mode`.

Brief 062 updates the loader to accept only that monotonic additive resume
shape. Any existing-value change, field removal, unexpected addition, wrong
thread, second rollout, missing context, or later `never` context still rejects.
The retained metadata evidence hash uses the latest complete record and the
runtime decision uses the latest persisted turn context with a before/after
stability check around the exact pinned `codex doctor` command.

Implementation `d404778509115290bf3a4918f52d6697b4b7faec` is confirmed on
`origin/codex/pi05-autolearn-loop`. One hundred seventy-seven focused tests
pass in each pinned robotics runtime. Compilation and `git diff --check` pass.
The broad offline authority/twin gate passes 376 tests in 102.558 seconds. A
real current-thread profile capture succeeds for thread `019f5372...`, turn
`7d245960...`, `approval_policy=on-request`, sandbox `danger-full-access`,
profile identity `4ade6d50...`, and `hardware_accessed=false`.

No live gate was opened. No USB, serial, camera, holder census, servo bus,
model, policy, replay, motion, optimizer, training, or paid compute ran.
Unrelated dirty paths remain unstaged and unchanged by this slice.
