# Session Log 273 - T20.36o Baseline Capture Runner

## Implementation

- Added the permit-bound T20.36o runner and deterministic signed contracts for
  attempt, tensors, denoise trajectories, scoring, result, and failure.
- Bound source construction seed 20260718, one X checkpoint load, the exact
  five-by-five-by-two probe order, noise-before-decode checks, start-zero-first
  hash acceptance, and complete ten-step path capture.
- Stored denoise state/velocity as exact signed float32 little-endian bytes so
  all 500 records remain remotely trackable and independently verifiable.

## Verification

- Exact permit materializer: `3d6a1548...`.
- Six focused baseline contract tests and 27 combined
  authority/contract/design/pointer tests pass.
- Both modified Python modules compile in the exact Python 3.12 environment.
- Live dataset-only preflight verifies starts 0/50/100/150/200, lengths
  50/50/50/50/44, five 50x6 targets, states, camera pixels, and tail masks.
- `git diff --check` passes.

## Result

Reviewer 270 verifies runner implementation only. No marker or model action
exists. The boundary must be remotely preserved before the one-use attempt.
