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
