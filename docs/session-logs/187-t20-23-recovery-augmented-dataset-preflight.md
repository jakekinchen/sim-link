# Session Log 187 - T20.23 Recovery-Augmented Dataset Preflight

## Scope

Brief 154 froze the next causal policy-data boundary after T20.17's learned
candidate failed strict contact. It materialized a local LeRobotDataset and
composed simulation-only training authority. No model, inference, optimizer,
rollout, hardware, camera, external compute, or Brev was used.

## Dataset And Provenance

- Nominal source: six T20.17 strict-success episodes, 1,464 frames.
- Recovery source: four T20.18 policy-visited strict-success recovery branches,
  866 frames.
- Persistent dataset: ten episodes, 2,330 frames, 30 Hz, two 256x256 RGB camera
  keys, six-joint state/action schema, measured actions, no padding or inference.
- Excluded evidence: T20.17 seeds 6-7 and T20.18's two near-failures / two
  failures, 424 frames total, remain outside training and statistics.
- No implicit resampling, duplication, reward weighting, or failure imitation.

## Evidence

- Dataset manifest identity:
  `f12c95a3cdf3e0005fa093000a5e44e1cddd08dbfb049ab405f462e2c9e760fa`.
- Dataset quantile-statistics identity:
  `d815dda101681ff394e2e211ca7936c90b08a259875ac49ff14319049f0e2669`.
- Training specification identity:
  `5ad2f407d5df49752c65180addbda033888fdcc5869fc5c9a546669bb94a58aa`.
- Owner grant identity:
  `efbf820ae0b1c2fe5771a030cd29e3089c3048ed4e77991c3008b703e0c9ddbb`.
- Authority request identity:
  `6845e479c3e858705e7383762b23df571f106a58e81f6461714d0b3a383182c2`.
- Authority decision identity:
  `6c2b822ce1d89aecea26d0914f1b3a503bd142d6f2feb62f4481fbda37a5dad5`.
- Implementation commit: `fc54988`.

The first materialization attempt failed closed before adding any recovery
episode because the durable package stores measured actions in radians while
the frame view stores rounded LeRobot values. Its 41 MB partial output was
preserved as `t20_23_recovery_augmented_dataset.incomplete_001`; the corrected
converter derives from measured radians and verifies the rendered view.

## Validation And Review

Five focused preflight/authority tests passed. A 46-test broad gate covered
artifacts, central authority, actual LeRobot manifests, simulation specs,
coordinates, T20.17 campaign/preflight, T20.19 ensemble, and T20.23. Five
T20.18 tests passed under the pinned MuJoCo runtime. Both the materialized
dataset/spec and central authority reverified exactly after review hardening.

Same-agent adversarial review covered source and outcome spoofing, duplicated
or overlapping branches, diagnostic/held-out leakage, frame/image count drift,
path escape and aliasing, image bytes/dimensions, non-finite values, radian-to-
LeRobot consistency, model/statistics drift, signed mutation, authority
escalation, and preservation of the failed partial output.

## Result

Reviewer Decision 184 verifies the dataset preflight and grants only central
`simulation_training_ready`. The frozen future campaign is local MPS, rank-4
LoRA, batch size one, and 500 updates, but no optimizer ran in this slice. A
new brief must activate training and preserve frozen seed-6/7 unassisted
strict-v2 evaluation. Physical transfer, promotion, hardware/camera access,
external compute, and Brev remain closed.
