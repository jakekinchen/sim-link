# Session Log 180 - T20.17 Source-Native Clean-Base Preflight

## Scope

Implementation commit `b826e3f` delivered the persistent dataset, clean-base
snapshot binding, fixed campaign specification, and central simulation-only
authority required before T20.17 optimizer execution. It did not load a model,
run inference, execute an optimizer or simulator rollout, access hardware, or
start external compute or Brev.

## Delivered

- One pinned LeRobotDataset at
  `outputs/robot_lab/t20_17_lerobot_training_dataset` with 6 source-native
  episodes and 1,464 frames from strict T17.5b seeds 0-5.
- Held-out seeds 6-7 remain raw source evidence outside the dataset and its
  statistics.
- Two unmodified source camera roles, six canonical SO-101 state/action
  dimensions, and measured-action semantics with no padding or interpolation.
- Signed LeRobot episode/content/metadata manifest and package quantile
  statistics identity.
- Complete cached `lerobot/pi05_base` binding, including the 14,467,165,872-byte
  weights blob with sha256
  `0eb11ca9587678c1d2ef8cf32807c29f8ce53a2bfdfc1aa4a4c96f16fca59b0f`.
- T20.17-specific owner grant, composition request, and central decision; only
  `simulation_training_ready` is granted.

## Validation

- Focused clean-base, native-manifest, simulation-authority, and central
  composer suite passed 26 tests.
- Python compilation passed for both modules and both command entrypoints.
- Live preflight verification reproduced training-spec identity
  `8898aeede6723c76f7bc2c38c8e922587a95fb14288cb672a855402b187d7df9`.
- Live central composition reproduced `simulation_training_ready` while
  withholding physical transfer and promotion.
- `git diff --check`, scoped staging, commit preservation, push, and remote HEAD
  equality passed at `b826e3f`.

## Adversarial Review

The same-agent review checked leakage of seeds 6-7 into package statistics,
source-byte or image substitution, duplicate or missing episodes, graph/path
aliasing, camera fabrication, padded joints/actions, non-finite values,
normalizer drift, partial model cache state, optimizer-budget escalation,
forged global authority, accidental hardware/external-compute state, and
cleanup side effects. The persistent dataset is fail-closed and is not
overwritten by the writer. Unrelated `.codex/config.toml` and vendored
checkouts remained uncommitted.

## Result

Brief 147 is verified by Reviewer Decision 177. The next T20.17 boundary may
load the bound clean base and run only the fixed local-MPS campaign after a new
brief activates that exact execution. No policy result or acceptance exists
yet.
