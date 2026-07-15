# Slice Brief 172 - T20.35f Normalized Residual And Saturation Audit

**Date:** 2026-07-15

**State:** `in_progress`

## Objective

Translate the immutable T20.35d wrist-roll and gripper residuals into the exact
PI0.5 action-normalization space, distinguish quantile-range exceedance from
actual clipping, and decompose retained five-seed error into systematic bias
and seed variance before authorizing any inference or training correction.

## Contract

- Bind T20.35e correction `f2a8aa80...`, T20.35d report `13b08e70...`, the
  T20.35c/T20.33 source-batch lineage, T20.17 dataset manifest `689516af...`,
  and exact local `meta/stats.json` hash `9c013fde...`.
- Bind the pinned PI0.5 configuration, normalizer, model sampler, and SceneSmith
  SO-101 coordinate-source hashes. Verify the active action mode is
  `QUANTILES`, using exact `q01`/`q99`, and record that this transform does not
  clip normalized targets.
- Convert the retained target and five decoded chunks from MuJoCo radians to
  LeRobot body degrees/gripper percent, then to normalized space. Preserve the
  exact 0.05-rad physical gate by deriving its channel-specific normalized
  equivalent and requiring the exceedance counts to remain 164 and 121.
- For wrist roll and gripper, report target values outside `[-1, 1]`, physical
  bound hits, normalized residual metrics, residual exceedances coincident with
  out-of-quantile targets, and the exact across-seed squared-error decomposition
  into mean-bias and population-variance terms.
- Treat any exact physical bound hit as clipping evidence. Otherwise, treat
  normalized target magnitude above one only as quantile-range exceedance, not
  saturation. If both selected channels have at least 75% of squared normalized
  error in the systematic-bias term, route a separately reviewed no-optimizer
  denoising-cadence discriminator against the pinned 10-step default. If seed
  variance exceeds 50% for either channel, route seed/noise stability instead;
  otherwise route a model-free normalization-coverage counterfactual.
- Run no model, inference, optimizer, checkpoint read/mutation, dataset write,
  rollout, hardware, external compute, or Brev.

## Acceptance Criteria

- Deterministic tests reject source identities/hashes, channel selection,
  source normalization semantics, malformed/non-finite matrices or statistics,
  gate/count drift, clipping relabeling, decomposition error, route drift, and
  forbidden-action drift.
- One signed audit is reproduced exactly from immutable sources and does not
  mutate the T20.35d report, T20.35e correction, dataset, or checkpoint.
- Focused and relevant broad tests, same-agent adversarial review, canonical
  state, ledger, session log, reviewer decision, scoped commits, and remote
  preservation agree.

## Out Of Scope

Model construction; inference; optimizer; training; checkpoint or dataset
mutation; denoising-cadence execution itself; normalization, coordinate,
threshold, or action correction; Gate C; rollout; hardware; external compute;
Brev; transfer; promotion; or policy acceptance.
