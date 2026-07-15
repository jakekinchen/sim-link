# Reviewer Decision 205 - Verify T20.35d Residual Localization

**Decision:** `ACCEPT_T20_35D_EXACT_REPLAY_AND_ROUTE_SEMANTIC_CORRECTION`

## Reviewed Boundary

Brief 170, implementation `7162497`, replay attempt `d3b3ff43...`, report
commit `806ac7f`, full signed report `13b08e70...`, tests, canonical state, and
scoped diff were reviewed together.

## Adversarial Findings

- The checkpoint tree was verified before the sole replay marker. All tensor
  keys, shapes, dtypes, counts, finite values, and expert-only parameter names
  passed before inference.
- All five horizon-50 decoded hashes reproduce T20.35c exactly. The small
  `~7e-18` alternate summation difference in one displayed mean is below the
  predeclared `1e-15` metric tolerance; the exact matrix hash is unchanged.
- The report retains complete target, decoded, and absolute-residual matrices
  plus all 366 coordinates above `0.05` rad. Seed counts are 52, 103, 67, 78,
  and 66, so no single inference seed explains the failure.
- Only 34/366 exceedances (9.29%) are in the first or last five timesteps;
  90.71% are interior. Chunk-boundary/cadence concentration is rejected for
  this one-batch decoder residual.
- Shoulder pan and elbow have zero exceedances. Shoulder lift has 29 and wrist
  flex 52. Wrist roll has 164 (44.81%) and gripper 121; together those two
  output channels hold 285/366 (77.87%).
- The predeclared classifier tests only one-joint (50%) and boundary (60%)
  concentration, so its signed `distributed_decoding_residual` label is
  mechanically correct but semantically under-specific for a dominant
  two-channel pattern. Its generic decoder/gate route must not be treated as a
  verified correction choice.
- No optimizer object, training, checkpoint mutation, rollout, policy
  acceptance, hardware, external compute, Brev, transfer, or promotion exists.

## Disposition

Accept the exact replay and residual measurements as verified. Open T20.35e as
an optimizer-free, model-free derived classification correction that preserves
report `13b08e70...` and adds an explicit top-two-channel concentration test.
Do not change training, the checkpoint, action decoding, thresholds, or Gate C
until that correction selects the next hypothesis.
