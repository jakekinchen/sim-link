# Brief 182 - T20.35p Terminal-Time Flow-Consistency Correction

## Objective

Test whether one bounded expert-only correction on T20.35o's exact late-step
model-visited states removes the terminal velocity-field error and passes Gate
B on the frozen one-batch target.

## Frozen Correction Set

- Source checkpoint: exact T20.35c expert-only checkpoint.
- Observation and deterministic target: exact T20.35c/T20.35o batch and
  processors.
- States: T20.35o pre-update states at inference steps 7, 8, and 9 for all five
  signed seeds, giving exactly 15 finite state/time examples.
- Target velocity: `(state-normalized_padded_target)/time` at each retained
  example.

The implementation may express each retained state through PI0.5's existing
flow-matching interface by deriving `noise=(state-(1-time)*target)/time`, but
must prove that the reconstructed state and target velocity match the signed
T20.35o tensors before any optimizer step.

## Bounded Discriminator

Freeze one explicit update count, constant learning rate, parameter boundary,
sample order, RNG seed, checkpoint output, and five-seed active-zero/padded-
normal evaluation in a signed training spec. Gate B still requires objective
ratio at most 0.10 and every decoded action within 0.05 rad; both conditions
must be recomputed without post-hoc action correction.

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

The correction set and reconstruction math verify exactly, all 15 examples are
used under the frozen schedule, objectives/gradients/checkpoint tensors remain
finite, and one signed result either passes Gate B or records the next smallest
evidence-routed blocker. No result implies policy acceptance or physical
transfer.
