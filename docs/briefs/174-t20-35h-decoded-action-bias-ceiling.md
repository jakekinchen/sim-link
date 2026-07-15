# Brief 174 - T20.35h Decoded-Action Bias Ceiling

## Objective

Determine whether T20.35g's repeatable decoded-action residual can be removed
by a simple output-bias class before any further model, optimizer, or training
work. This is a model-free analytical ceiling, not a policy correction.

## Frozen Sources

- T20.35g signed result identity `57f1f0dd5190fa1e0dc2b84cf25546b8f4e520bb75d2a15616797c5f311b2ea2`.
- The exact 10-step baseline row and its five decoded chunk hashes.
- The exact 50-by-6 target action chunk already bound through T20.35d/g.
- Seeds `20260721` through `20260725`, in that order.
- Physical action-error threshold `0.05` rad.

The source result must verify before calculation, and its 10-step hashes and
metrics must reproduce exactly. The 20- and 50-step rows are evidence for the
cadence rejection only and are not correction inputs.

## Correction Classes

For each held-out seed, use only the other four seeds as calibration rows.
Define residual as `target - decoded_action`.

1. `global_output_channel_bias`: average residual over all calibration seeds
   and all 50 timesteps separately for each of the six channels; apply that
   single six-value vector to every held-out timestep.
2. `time_conditioned_output_channel_bias`: average residual over calibration
   seeds separately for every timestep and channel; apply that 50-by-6 matrix
   to the held-out chunk.

The held-out chunk may not contribute to its correction. No clipping,
projection, fitted scale, candidate search, seed dropping, channel dropping,
or threshold adjustment is allowed.

## Evidence And Routing

Record each fold's calibration seeds, correction hash, corrected chunk hash,
per-channel maximum/mean errors, total threshold exceedances, chunk maximum,
and chunk mean. Record worst-fold maximum and aggregate mean for each class.

- A class passes its analytical ceiling only if every corrected held-out chunk
  has maximum absolute error at or below `0.05` rad.
- Prefer the global class if it passes. Otherwise prefer the time-conditioned
  class if it passes.
- If neither passes but the time-conditioned class strictly improves both the
  baseline worst-fold maximum and aggregate mean, route residual-variance
  localization before a model correction.
- Otherwise reject bias-only correction and route representation/action-head
  localization.

Regardless of outcome, set `gate_b_passed=false`,
`action_correction_selected=false`, and `simulation_policy_accepted=false`.
A later model-internal correction must earn Gate B independently.

## Prohibited Actions

- Model construction, checkpoint tensor access, or inference.
- Optimizer creation, training, continuation, or statistics changes.
- Dataset/checkpoint/source mutation or rewriting T20.35g.
- Closed-loop rollout, Gate C work, policy acceptance, or promotion.
- Hardware, camera, serial, external compute, or Brev access.

## Acceptance

- Deterministic adversarial tests cover source drift, seed/order/shape drift,
  held-out leakage, non-finite values, correction formulas, hashes, gates,
  route priority, forbidden truth claims, and verifier replay.
- The signed artifact verifies exactly from immutable sources.
- Focused tests, the relevant T20.33-35 regression gate, pointer check, and
  workflow audit pass.
- Same-agent adversarial review, scoped commit, push, and remote confirmation
  agree before the next task opens.
