# Reviewer Decision 304 - Verify T20.43b Administrative Authority Refresh

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43B_EPOCH_2_IMPLEMENTATION_FOR_MODEL_FREE_MATERIALIZATION_AFTER_ORIGIN`

The complete Brief 225 scoped diff is accepted for origin preservation. It
adds a separately named epoch-2 administrative wrapper around the unconsumed
T20.43b ACT replacement without changing any training or evaluation factor.

## Verified invariants

- Epoch-1 spec `13c5bb4b...`, Gate A `ea65f3d1...`, renderer smoke
  `35224058...`, owner grant `09111fcb...`, central decision `3b534f91...`,
  runtime `549c0db2...`, permit `c7e8e1ca...`, acceptance `525de8dc...`, and
  Reviewer 302 bytes remain immutable at their existing paths.
- The wrapper fixes refresh epoch 2, replacement ordinal 1, attempt ordinal 1,
  one authorized attempt, and no retry. It reuses the same sole marker and run
  paths; it cannot represent a second replacement or second attempt.
- The central composer reconstructs all seven simulation prerequisites and can
  grant only `simulation_training_ready` for a fresh interval of at most eight
  hours.
- Runtime materialization must occur through the stable LeRobot interpreter,
  prove MPS/dependency/cache/support-tree continuity, confirm the reviewed
  implementation on origin, re-hash every immutable epoch-1 artifact, and
  prove every marker/run/result path absent and unaliased.
- The runner now requires the epoch-2 permit and separately reviewer-bound
  epoch-2 acceptance. It still writes the original marker before any backbone
  tensor read, model action, inference, optimizer, or Gate C rollout.

## Verification

- 4 epoch-2 contract tests pass, including rejection of an eight-hour-plus-one-
  second interval, marker presence, immutable-base drift, and attempt-count
  drift.
- 34 T20.43/T20.43b/T20.44 focused and regression tests pass.
- 42 artifact, central-authority, pointer-sync, and quantitative-receipt tests
  pass.
- Offline Ruff check and format check pass for all five changed Python/test
  surfaces. Python compilation, all three CLI help/import probes, strict JSON,
  whitespace, and `git diff --check` pass.

## Adversarial review

The review specifically checked stale epoch-1 reuse, path aliasing, marker
collision, output collision, source or cache drift, evidence substitution,
authority escalation, second-attempt encoding, retry, recipe mutation,
non-finite-value bypass, post-marker cleanup, and concurrent unrelated dirty
paths. All authority/output writes are exclusive; base artifacts are only
read and re-hashed; unrelated K1, external, temporary, and Codex-config dirt is
outside this scope and remains untouched.

## Authority granted

After this implementation and its synchronized state are exact on
`origin/codex/pi05-autolearn-loop`, materialize one model-free epoch-2 owner,
central request/decision, runtime, and permit bundle for a fresh same-agent
pre-run review.

## Authority withheld

No marker, backbone/model tensor read, model construction/load/inference,
optimizer, checkpoint, rollout, Gate C result, retry, second replacement,
recipe/schedule/threshold change, hardware/camera/serial access, physical
motion, network/package installation, external compute, Brev, transfer,
promotion, or destructive operation.
