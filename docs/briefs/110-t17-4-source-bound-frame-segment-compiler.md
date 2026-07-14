# Slice Brief 110 - T17.4 Source-Bound Frame And Segment Compiler

**Date:** 2026-07-13

## Objective

Compile the immutable T17.1 raw-rollout/frame projection into deterministic
source-bound frame and hard-boundary segment tables while quarantining records
that do not retain the per-frame evidence required for training.

## Contract

- Bind compilation to the current T17.1 experience-record identity
  `8682cea5d45ed5cf115f3f68eadc5f81376e26b9d6981969876f05c3c7665737` and the
  current T17.3 normalization-bundle identity
  `dea3ff8cb85640499416fc6fd6bf0cf43dce3479766fb1ff277e8d224e097ebe` without
  applying normalization or claiming production readiness.
- Emit deterministic `frames.parquet`, `segments.parquet`,
  `quarantine_manifest.json`, and `compiler_manifest.json` under the T17.4
  artifact directory.
- Preserve raw rollout/frame identities, source pointers, provenance, action
  variants, requested-versus-executed distinctions, and unavailable-value
  reasons. Never rewrite raw bytes or infer missing actions.
- Split or quarantine on rollout/reset/teleport/scene/prompt/controller,
  control-mode, coordinate-contract, dropped-observation, timestamp-gap, or
  other declared hard-boundary events. Unknown semantics fail closed.
- Emit no training windows, no optimizer authority, and no physical or Brev
  work. The current two-frame fixture must produce frame rows plus explicit
  quarantine and no eligible segment rows because its action evidence is
  unavailable.

## Verification

- Deterministic second compile is byte-identical for all outputs.
- Current fixture is self-verified and quarantined for incomplete per-frame
  action/gripper/effort evidence and missing hard-boundary compilation.
- Synthetic complete records are used only in unit tests to prove positive
  segmentation and negative boundary/gap cases; they are never labeled as
  production or training evidence.
- Focused tests, the relevant broad gate, state-pointer check, artifact hashes,
  same-agent adversarial review, scoped commit, and remote confirmation must
  all agree before T17.4 is marked verified.

## Verified Outcome

- Compiler implementation is committed and remotely confirmed at
  `1a3746613d5856db05c901ba51e92dbdb7756c8d`.
- The current source projection emits 2 frame rows, 0 eligible frames, 0
  segments, and 2 explicit frame quarantine entries. The output hashes are
  `frames.parquet` `ba9c4523a80588eceded8e93cb39ea1dd8aebe62bcca06a6741ce732ec52926b`,
  `segments.parquet` `44230e200794b46d70f02654be0e470341eefa6f479fa113649f0de8d62d5446`,
  `quarantine_manifest.json`
  `0bc52a76729919603cdb894071fe47250d3eddaaa996df33ab76dcb291581748`,
  and `compiler_manifest.json`
  `48974083098f3bf3295839303810ebf5c8ed3e672985c0807253e288d5eef1e6`.
- The quarantine manifest retains missing action variants, requested/achieved
  gripper pose, and effort reasons. Frame rows retain canonical JSON for the
  complete raw action/gripper/provenance fields, plus source and rollout
  identities; raw bytes are not rewritten.
- Synthetic unit fixtures prove positive segmentation, hard-boundary splitting,
  timestamp-gap rejection, and that a quarantined frame cannot bridge two
  eligible segments. Final scoped gates pass: 44 contract/compiler/pointer
  regression tests, 4 compiler tests, all three canonical writer `--verify`
  checks, `uv lock --check`, and the project-state pointer check.
- A same-agent review accepted the boundary as Reviewer Decision 138. The
  repository-wide unit invocation remains environment-limited at 616 tests
  with 69 pre-existing dependency-import errors in the incomplete local
  environment; no compiler test failed in that run.
