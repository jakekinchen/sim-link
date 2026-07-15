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

## Pre-Run Boundary

Implementation `bac3877` plus wrapper normalization `ef90668`, signed spec
`70be21a2...`, and central authority decision `f4ef827b...` are remotely
preserved. All 50 exact T20.35q states reconstruct below `1.2e-15`; each is
scheduled exactly 10 times over 500 AdamW updates at `2.5e-5`. Gate B retains
the original standard-objective baseline and 0.05-rad all-seed action gate.
Reviewer 227 authorizes one Python 3.12 local-MPS training/evaluation attempt.
No T20.35r model load, inference, optimizer creation, training, rollout, Gate
C, hardware, external compute, or Brev action occurred before authorization.

## Result

The sole attempt `fbcc16a5...` produced run `85826156...`, checkpoint
`b73123dc...`, and signed result `52d4c9ed...`, remotely preserved at
`c8f75a0`. The correction objective improves to ratio `0.095317`, but the
standard objective rises to original-baseline ratio `0.150468` and every
decoded chunk fails 0.05 rad with maxima `0.114470–0.197005`. Reviewer 228
verifies the negative result, keeps Gate B and Gate C closed, and opens
T20.35s under Brief 185 for a model-free time-step objective-mass and
standard-compatibility audit.
