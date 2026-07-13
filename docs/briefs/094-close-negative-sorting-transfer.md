# Slice Brief 094 - Close Negative Sorting Transfer

**Date:** 2026-07-13

## Objective

Close T16.5c as a verified diagnostic experiment with a negative sorting-
checkpoint transfer result, while preserving its useful preprocessing and
failure-diagnosis artifacts and withholding every deployment, motion,
qualification, and training claim.

## Contract

- Reverify the accepted static-pose observation, current-frame preprocessing,
  deterministic MPS proposal, and coordinate-corrected simulation consequence
  replay chain already accepted through Reviewers 112-114.
- Preserve the sorting checkpoint as a preprocessing and failure-diagnosis
  regression fixture; do not relabel it as an accepted grasp policy.
- Record separate foundational implementation, latest task-level
  implementation, and T16.5c negative-experiment closeout boundaries.
- Set T16.5c to `verified` only with this exact result: physical observation
  and deterministic no-actuation checkpoint diagnosis completed; sorting
  checkpoint rejected for this physical scene and camera domain.
- Grant only physical static-pose observation validity, physical camera-role
  mapping validity, diagnostic physical preprocessing validity, observed
  diagnostic policy proposal, and observed coordinate-corrected simulation
  consequence replay.
- Withhold accepted sorting-policy input for deployment, matched physical
  replay, physical actuation, physical transfer, physical qualification, and
  training authority.
- Move the active program to a grasp-focused M17/M19 execution track with the
  live gate and training lock closed.

This slice changes canonical workflow state and closeout documentation only.
It does not access hardware, run inference, train, or alter the historical
Briefs 087-093 and their evidence.

## Verified Outcome

- The accepted static-pose bracket, stable camera roles, preprocessing,
  deterministic MPS proposal, and corrected MuJoCo consequence replay retain
  their recorded identities and file hashes.
- Both pinned runtimes pass the same 102-test focused regression gate; the
  static-pose source and candidate-source verifiers pass without hardware
  enumeration or access.
- T16.5c closes as a successful diagnostic experiment with a negative transfer
  result. The sorting checkpoint remains a regression fixture and is not an
  accepted grasp or deployment policy.
- The live gate and training lock remain closed.
