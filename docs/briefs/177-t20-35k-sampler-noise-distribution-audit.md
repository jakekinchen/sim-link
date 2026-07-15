# Brief 177 - T20.35k Sampler And Noise-Distribution Audit

## Objective

Explain T20.35j's monotonic improvement under reduced initial noise by auditing
the exact active PI0.5 training and inference source without importing or
loading the model. Determine whether the default sampler contract is mismatched
or whether noise enters unsupervised padded action dimensions.

## Frozen Sources

- T20.35j signed result `e9bbff84864a838f64e67c72a4996fd4eefe13739294becc43a371268f3da75a`.
- Active Python 3.12 PI0.5 model source hash `006fee5765b235dd66c55f16d78a1e296dc320667a02608c68a057d72d70bde0`.
- Active PI0.5 configuration source and its exact hash.
- Six source action channels, configured `max_action_dim=32`, chunk length 50,
  and 10 inference steps.

## Required Mechanical Audit

Parse the exact source and emit a signed report that fails closed on source or
lineage drift. Record and verify:

- the sampler distribution and parameters;
- training noise construction, time distribution, interpolation, and velocity
  target;
- inference initial state, Euler step, and time grid;
- training action padding and inference noise width;
- loss truncation and returned-action truncation widths;
- whether active and padded dimensions share the same action projection input.

The report must distinguish six supervised returned channels from 26 padded
channels. It must not infer that padded dimensions cause the observed error
merely from source exposure; that requires a later controlled discriminator.

## Routing

- A true train/inference distribution mismatch routes source correction.
- A matched sampler with stochastic padded dimensions entering the action
  projection while loss is truncated routes one separately reviewed
  active-versus-padded noise-mask discriminator.
- A matched sampler without padded exposure routes a model flow-consistency
  audit.

## Prohibited Actions

No model import/load/inference, checkpoint or dataset access, source mutation,
sampler change, optimizer, training, rollout, Gate C, hardware, camera, serial,
external compute, or Brev. This audit cannot pass Gate B or accept a policy.

## Acceptance

Deterministic tests cover exact source hashes, AST semantics, dimensional
arithmetic, route selection, malformed/non-finite inputs, signed identity, and
all forbidden truth flags. Writer verification must reproduce the checked-in
report under both configured Python runtimes before same-agent review.

## Result Boundary

Audit `bc9f0845...`, preserved at `357cd6e`, verifies a matched standard-normal
training/inference sampler plus 26 stochastic padded dimensions that enter the
shared action projection without direct output loss. Reviewer 215 routes only
the separately reviewed T20.35l active-versus-padded noise-mask discriminator.
The audit itself does not claim causality, pass Gate B, or authorize Gate C.
