# Brief 175 - T20.35i Residual-Variance Localization

## Objective

Localize the residual seed variance left after T20.35h's time-conditioned
leave-one-seed-out bias correction, without loading a model or testing another
correction. The result must distinguish seed, channel, boundary, and
distributed sampling sensitivity before any inference or optimizer rung.

## Frozen Sources

- T20.35h artifact identity `63e1181b2f825de108a85525e38e0ae728cae2288a16b7d3763851e8109a6593`.
- T20.35g result identity `57f1f0dd5190fa1e0dc2b84cf25546b8f4e520bb75d2a15616797c5f311b2ea2`.
- Exact 10-step decoded chunks, target, five seeds, held-out calibration rule,
  correction hashes, and corrected-chunk hashes.
- Physical error threshold `0.05` rad and action horizon 50.

The implementation must rebuild every time-conditioned fold and reproduce all
five correction/corrected hashes before localizing an error.

## Required Evidence

- Every corrected element above `0.05` rad with seed, timestep, channel,
  signed/absolute error, target, corrected action, and raw decoded spread.
- Counts and fractions by seed, channel, seed-channel pair, and timestep.
- First/last-five-timestep boundary count and fraction.
- Single and top-two seed/channel concentration summaries with deterministic
  tie-breaking by seed order or channel index.
- Per-timestep/channel raw five-seed range, maximum range, aggregate mean
  range, and unique positions associated with at least one held-out failure.
- The identity `held_out_error = 5/4 * (raw_seed_value - raw_seed_mean)` must
  hold within `1e-15` for every element.

## Frozen Classification And Routing

- Boundary concentration threshold: 60%.
- Single-seed or single-channel threshold: 50%.
- Top-two-seed or top-two-channel threshold: 75%.
- Precedence: boundary, single seed, top-two seeds, single channel, top-two
  channels, then distributed seed/channel variance.
- Boundary routes sampler time-grid localization.
- Seed concentration routes an inference-only initial-noise sensitivity probe.
- Channel concentration routes action-head stochastic-channel localization.
- Distributed variance routes one separately reviewed inference-only
  initial-noise-scale discriminator.

This task always records `gate_b_passed=false` and
`action_correction_selected=false`; it localizes evidence only.

## Prohibited Actions

- Model construction, checkpoint tensor access, inference, or sampling.
- Optimizer creation, training, continuation, or statistics changes.
- Source/dataset/checkpoint mutation or post-hoc correction selection.
- Closed-loop rollout, Gate C, policy acceptance, promotion, hardware,
  external compute, or Brev.

## Acceptance

- Deterministic tests cover source/hash drift, fold reconstruction, the 5/4
  identity, non-finite data, all classification branches and precedence,
  route/flag mutation, counts, tie-breaking, and verifier replay.
- The signed artifact verifies in both configured Python runtimes.
- Focused and relevant T20.33-35 tests, pointer check, workflow audit,
  same-agent adversarial review, scoped commit, push, and remote confirmation
  agree before another task opens.
