# Reviewer Decision 177 - Verify T20.17 Source-Native Clean-Base Preflight

`CONTINUE_T20_17_BOUNDED_CLEAN_BASE_CAMPAIGN`

Reviewed implementation commit `b826e3f` under Brief 147.

The implementation creates one persistent pinned LeRobotDataset from T17.5b
seeds 0-5 and keeps seeds 6-7 outside both the dataset and its statistics. The
package dataset contains 6 episodes and 1,464 frames, preserves the two source
PNG cameras and six-joint measured-action semantics, and uses the existing
MuJoCo-to-LeRobot coordinate bridge without padding or inferred actions.

The signed specification binds package metadata/statistics, all package episode
content, raw source identities, held-out raw bytes, and the complete local
`lerobot/pi05_base` snapshot at revision
`7de663972b7817d2c4cf2d84c821153dfea772e9`. The future campaign is fixed at
rank-4 LoRA, local MPS, batch size 1, 250 updates, seed 20260714, package
quantile statistics, and strict seed-6 evaluation.

Adversarial review checked source/held-out leakage, duplicate seeds, non-finite
values, image-byte substitution, camera fabrication, action padding,
coordinate drift, cache aliasing, partial model bytes, campaign inflation,
owner-grant drift, global-authority forgery, and unintended cleanup. The
focused manifest, authority, and composition suite passed 26 tests; both live
preflight and live authority re-verification passed. Central composition grants
only `simulation_training_ready`; physical transfer and promotion remain
withheld.

This decision verifies the preflight boundary only. It does not itself record
optimizer execution, model inference, strict-v2 policy success, policy
acceptance, physical transfer, promotion, hardware access, external compute,
or Brev authority. A new precise brief is required before the bounded local
campaign starts.
