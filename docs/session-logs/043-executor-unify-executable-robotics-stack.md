# Executor Session 043 - Unify Executable Robotics Stack

**Date:** 2026-07-10

## Slice

Replace the T16.1 `split_runtime_unresolved` acceptance with one fail-closed
SceneSmith LeRobot executable identity shared by collection, training,
finalization, inference, and LeLab launch paths.

## Implementation

- Pinned LeRobot base commit
  `e40b58a8dfa9e7b86918c374791599d070518d11`.
- Repaired the tracked patch so it applies cleanly to that base and exactly
  reproduces the active checkout, including the previously omitted red-task
  sampling change. Patch-set identity:
  `efe912e3cf75c76a3b0a01d2baec8f0856ce2e2a981f4845978f0e9e34155284`.
- Added tracked critical environment defaults, processor contract, and LeRobot
  `uv.lock` identity
  `367f3d6635ce0975bff459a02ea01ecd847836f491223c5394253d7d054b9280`.
- Added a shared activator that rejects base, patch, lockfile, environment, or
  already-imported-package drift before any stage imports LeRobot.
- Bound SceneSmith collection, training, finalization, inference, merge/relabel,
  and LeLab wrapper entrypoints to that activator.
- Replaced the dependency-lock resolution with
  `exact_base_plus_tracked_patchset` and recorded LeLab's effective unified
  runtime rather than accepting its divergent source declaration as executable.
- Added a saved-sample parity gate across collection/training/inference boundary
  processing. Composite stack identity:
  `c8e903e7f1b75215864719398c902d864d8cbd7f43e01f03ffb22c8de240a7a4`.
- Regenerated every deterministic downstream artifact whose dependency-lock
  reference changed, including the synthetic fixture linkage. Historical
  T16.4 synthetic ready identity rekeyed to
  `c3d3c93e88559167aa7059cb00fadb94ed8a0f1084d81697f2e22ffaab70fe41`
  without changing its golden aggregate physics.

## Validation

- Clean-base `git apply --check` passed for the tracked patch.
- Tracked patch bytes exactly equal `git diff --binary HEAD --` in the active
  LeRobot checkout.
- `python scripts/robot_lab/verify_lerobot_stack.py` passed saved-sample parity.
- LeLab wrapper imported LeRobot from
  `external/lerobot/src/lerobot/__init__.py`.
- Focused executable-stack and dependency-lock suite passed 13 tests.
- Twin contract suite passed 13 tests.
- Structural twin suite passed 24 tests.
- Measured-inertial suite passed 24 tests in 37.145 seconds.
- All touched Python entrypoints passed `py_compile`; Brev shell entrypoints
  passed `bash -n`; all regenerated artifact verifiers passed; `git diff
  --check` passed.

## Authority

This slice grants a reproducible executable-stack identity. It does not grant
optimizer, simulation-training, physical-transfer, or promotion authority.
`training_lock` remains closed.

## Next Slice

Independent review of T16.1b, then T16.4b strict production measured-inertial
intake and authority separation.
