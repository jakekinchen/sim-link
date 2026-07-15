# Reviewer Decision 207 - Verify T20.35f Normalized Residual Audit

**Decision:** `ACCEPT_T20_35F_SYSTEMATIC_BIAS_ROUTE_DENOISING_CADENCE`

## Reviewed Boundary

Brief 172, implementation and artifact commit `dea54fb`, audit `85c24c5c...`,
immutable T20.35d report `13b08e70...`, T20.35e correction `f2a8aa80...`,
exact T20.17 action statistics, pinned source hashes, tests, canonical state,
and scoped diff were reviewed together.

## Adversarial Findings

- The audit binds the complete T20.33-to-T20.35f lineage and verifies the exact
  T20.17 `meta/stats.json` file hash recorded by the signed dataset manifest.
- The pinned PI0.5 action mode is QUANTILES with q01/q99 scaling and no
  normalized-value clipping. The pinned sampler default is 10 denoising steps.
  SceneSmith coordinate conversion is source-hash bound.
- The 0.05-rad gate converts to 0.069291 normalized wrist-roll units and
  0.074033 normalized gripper units. Counts reproduce exactly at 164 and 121;
  no gate or threshold was relaxed.
- Wrist-roll targets lie outside `[-1,1]` on 39/50 timesteps; 142/164 residual
  exceedances coincide with those timesteps. Gripper is outside on 32/50;
  74/121 exceedances coincide. These are quantile-range exceedances, not proof
  of clipping.
- Target and decoded physical-bound hit counts are zero for both channels, so
  hard saturation and coordinate-output clipping are rejected on this evidence.
- Across five retained seeds, systematic mean-bias explains 84.81% of
  wrist-roll normalized squared error and 82.33% of gripper error. Seed
  variance explains only 15.19% and 17.67%. Both clear the predeclared 75%
  systematic-bias threshold; neither approaches variance dominance.
- Three focused and 84 relevant tests pass, including identity/hash, malformed
  source, channel selection, quantile, count, decomposition, clipping-route,
  cadence-route, noise-route, non-finite, and forbidden-action cases.
- No model load, inference, optimizer, checkpoint read or mutation, dataset
  write, rollout, Gate C work, hardware, external compute, Brev, transfer,
  promotion, or policy acceptance occurred.

## Disposition

Accept T20.35f as verified. Open T20.35g only as a separately reviewed,
inference-only denoising-cadence discriminator using the immutable expert-only
checkpoint, exact batch, and fixed five seeds against the 10-step default. Do
not train, change normalization, select a correction, or enter Gate C yet.
