# Brief 190 - T20.35x Physical-Gate-Aligned Joint-Weighted Correction

## Objective

Test whether aligning full-path supervision with the unchanged uniform
0.05-rad physical action gate removes T20.35w's shoulder-lift/wrist-roll error
dominance while retaining T20.35t's standard-objective pass.

## Frozen Sources

- Start from exact T20.35t checkpoint `aeef380b...`, which passes raw
  correction and original-baseline standard-objective ratios.
- Use all 50 exact T20.35v current-policy states, five seeds by ten denoise
  steps, and the same deterministic normalized target and flow reference.
- Derive six active-joint physical-radian Jacobian weights only from the exact
  dataset action normalizer and SO-101 coordinate contract; bind every source
  statistic and weight in the spec.

## Correction Contract

At each V state, weight active-dimension squared flow error by normalized
physical-radian Jacobian squared; retain padded-dimension coefficient 1.0.
Then derive ten time weights that equalize the initial per-step mean of this
joint-weighted objective. Pair every correction gradient with one unique
deterministic standard one-batch replay gradient before stepping. Freeze the
source checkpoint, 50-example schedule, 500 constant-LR AdamW updates at
`2.5e-5`, expert-only parameter boundary, seeds, processors, sampler, and Gate
B evaluation. Record raw, joint-weighted, time-and-joint-weighted, standard,
and combined objectives so weighting cannot conceal regression.

## Gates

Gate B remains unchanged: standard-objective ratio at most 0.10 of the
original baseline and every decoded action chunk at most 0.05 rad. Weighted
correction improvement alone cannot pass or open Gate C.

## One-Use Boundary

Tests, implementation, signed spec, central simulation-training authority,
immutable attempt semantics, exact dependency-complete runtime preflight,
same-agent adversarial review, scoped commit, push, and remote confirmation
must precede checkpoint tensor access, model construction, or optimizer
creation. A fresh reviewer decision may authorize exactly one local-MPS
training/evaluation attempt.

## Prohibited Actions

No source/result mutation, retry, extra state/seed/time, objective/gate change,
rollout, Gate C, hardware, camera, serial, external compute, or Brev.

## Acceptance

All physical joint weights, time weights, 50 examples, 500 paired updates,
objectives, gradients, checkpoint tensors, and five Gate B chunks verify
exactly and remain finite. One signed result either passes Gate B or records
the next smallest evidence-routed blocker. No result implies closed-loop or
physical policy success.
