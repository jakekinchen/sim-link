# Brief 184 - T20.35r Full-Path Self-Consistency Correction

## Objective

Test whether one bounded expert-only correction on T20.35q's exact
self-generated 10-step paths removes the early/mid denoising-field
interference and passes Gate B on the frozen one-batch target.

## Frozen Correction Set

- Source checkpoint: exact T20.35p checkpoint `9358cee4...`.
- Observation and deterministic target: exact T20.35p/T20.35q batch and
  processors.
- States: all 10 T20.35q pre-update states for each of five signed seeds,
  giving exactly 50 finite state/time examples.
- Target velocity: `(state-normalized_padded_target)/time` at every retained
  example.

Each retained state must reconstruct through PI0.5's existing flow-matching
interface before optimizer creation. The signed training spec must freeze 500
constant-LR expert-only updates at `2.5e-5`, a balanced schedule using every
example exactly 10 times, the exact parameter boundary, RNG seed, checkpoint
output, and the five-seed active-zero/padded-normal evaluation.

## Gates

The correction-set objective must improve deterministically. Gate B remains
unchanged: the original standard-objective ratio must be at most 0.10 and all
five decoded action chunks must have maximum absolute error at most 0.05 rad.
No post-hoc action correction is permitted.

## One-Use Boundary

Tests, implementation, central simulation-training authority, signed spec,
immutable attempt semantics, same-agent adversarial review, scoped commit,
push, and remote confirmation must precede model loading or optimizer
creation. A new pre-run reviewer decision may authorize exactly one local-MPS
training/evaluation attempt.

## Prohibited Actions

No source/result mutation, retry, extra state/seed/time, sampler or processor
change, rollout, Gate C, hardware, camera, serial, external compute, or Brev.

## Acceptance

All 50 examples reconstruct exactly and are used under the frozen schedule;
objectives, gradients, and checkpoint tensors remain finite; the source
checkpoint stays unchanged; and one signed result either passes Gate B or
records the next smallest evidence-routed blocker. No result implies
closed-loop policy acceptance or physical transfer.
