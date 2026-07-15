# Brief 181 - T20.35o Flow-Trajectory Consistency Audit

## Objective

Locate where the expert-only checkpoint's learned 10-step velocity field departs
from the exact deterministic single-target straight flow under T20.35n's best
active-zero/padded-normal condition.

## Frozen Sources And Condition

- T20.35n result `d3e6e5d9...` and its inherited active-zero/padded-normal
  chunks from T20.35l.
- Exact checkpoint, batch/target, normalization, processors, five base-noise
  tensors, 10 inference steps, and active/padded dimensions.
- Active dimensions 0-5 start at zero; padded dimensions 6-31 retain the exact
  standard-normal base noise.

The run must reproduce all five signed decoded-action hashes before trajectory
metrics are interpreted.

## Reference And Evidence

At every pre-update state `x_t` with `t>0`, compare learned velocity `v_t` with
the deterministic single-target straight-flow reference `(x_t-target)/t`.
Record finite per-step active-channel residual matrices, their hashes and
max/mean summaries, padded-dimension max/mean summaries, and exact state/velocity
hashes. Bind the normalized padded target used by the reviewed runner.

Classify whether active residual is late-step concentrated, channel
concentrated, or distributed. This is diagnostic evidence, not a post-hoc
action correction or proof that the model should use zero active noise.

## One-Use Boundary

Implementation, spec, one-use permit, tests, same-agent review, commit, push,
and remote confirmation must precede model or checkpoint tensor access. The
runner writes an immutable attempt marker before model loading.

## Prohibited Actions

No source mutation, optimizer, training, checkpoint/dataset mutation, action
correction, extra condition/seed/step, rollout, Gate C, hardware, camera,
serial, external compute, or Brev.

## Acceptance

Tests cover exact lineage, target and trajectory dimensions, reference-velocity
math, residual hashes and summaries, decoded endpoint reproduction,
classification thresholds, one-use semantics, non-finite values, and all
forbidden truth flags. A fresh pre-run decision must authorize exactly one
Python 3.12 local-MPS inference attempt.

## Pre-Run Boundary

Implementation `100a76e`, spec `c21c4d48...`, and one-use permit
`65c516f3...` are remotely preserved. Reviewer 221 accepts the same-agent
adversarial review and authorizes exactly one Python 3.12 local-MPS
model-load/inference attempt. The reviewed boundary retains raw finite states
and learned velocities so every reference residual, hash, summary, and route is
recomputed by the verifier. Eleven relevant tests pass. No model, checkpoint
tensor, inference, optimizer, mutation, rollout, Gate C, hardware, external
compute, or Brev action occurred before authorization.

## Result

The sole attempt `5161631f...` produced signed result `5c5b41b9...`, remotely
preserved at `30b5b0a`. All five decoded endpoints reproduce exactly. Active
residual mean rises from `0.033131` at time 1.0 to `0.368387` at time 0.1;
`62.8898%` of active residual mass lies in the final three steps, while no
channel exceeds `24.7865%`. Reviewer 222 verifies a late-step distributed flow
residual, keeps Gate B and Gate C closed, and routes T20.35p under Brief 182.
