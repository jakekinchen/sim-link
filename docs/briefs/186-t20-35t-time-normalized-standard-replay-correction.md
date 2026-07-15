# Brief 186 - T20.35t Time-Normalized Standard-Replay Correction

## Objective

Test whether time-normalizing T20.35q's full-path correction objective while
replaying the original standard one-batch objective removes T20.35s's proven
late-time objective-mass dominance and standard-objective interference.

## Frozen Sources

- Start from the exact T20.35p checkpoint `9358cee4...`, before T20.35r's
  standard-objective regression.
- Reuse the exact 50 T20.35q state/time examples, deterministic target,
  processors, active-zero/padded-normal evaluation, and five seeds.
- Bind T20.35s audit `113f72a9...` and recompute all time weights from its
  immutable T20.35r baseline objective values.

## Correction Contract

For each denoise step, weight correction loss by the global baseline
correction mean divided by that step's baseline mean. This makes every step's
initial weighted mean equal while preserving the overall baseline scale.
Freeze 500 constant-LR AdamW updates at `2.5e-5`, use every correction example
exactly 10 times, and accumulate one weighted correction gradient plus one
deterministically seeded standard one-batch gradient before each optimizer
step. Both terms have coefficient 1.0.

The signed spec must freeze every per-step weight, correction order, standard
replay seed, optimizer field, expert-only parameter boundary, output path, and
Gate B evaluation. Record raw and weighted correction objectives plus standard
objectives so the verifier can distinguish balancing from concealment.

## Gates

Gate B remains unchanged: final standard-objective ratio at most 0.10 of the
original baseline and every decoded action chunk at most 0.05 rad. Weighted or
raw correction improvement alone cannot pass.

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

All weights and 50 examples recompute exactly; all 500 paired terms execute
under the frozen schedule; objectives, gradients, and checkpoint tensors stay
finite; and one signed result either passes Gate B or records the next
smallest evidence-routed blocker. No result implies closed-loop or physical
policy success.

## Pre-Run Boundary

Implementation `545a563`, signed spec `34881e21...`, and central authority
decision `8387945b...` are remotely preserved. Ten exact time weights make
each step's initial weighted correction mean equal to `0.120801`; all 50
examples appear 10 times, and every update has one unique frozen standard
replay seed. Reviewer 230 authorizes one Python 3.12 local-MPS
training/evaluation attempt. Fifty-four relevant tests pass. No T20.35t model
load, checkpoint tensor access, inference, optimizer creation, training,
rollout, Gate C, hardware, external compute, or Brev action occurred before
authorization.
