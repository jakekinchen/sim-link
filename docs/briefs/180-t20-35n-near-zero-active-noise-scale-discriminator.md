# Brief 180 - T20.35n Near-Zero Active-Noise Scale Discriminator

## Objective

Test whether a small amount of active-six prior noise improves on T20.35l's
best active-zero/padded-normal condition enough to pass Gate B, while keeping
the padded 26 dimensions at their standard-normal prior.

## Frozen Sources And Conditions

- T20.35l result `b4fc6060...` and T20.35m audit `83105424...`.
- Exact expert-only checkpoint, one batch/target, processors, five seeds,
  standard-normal base tensors, 10 steps, and 0.05-rad gate.
- Padded dimensions 6-31 remain scale 1.0 for every condition.
- Inherited active scales: `0.0` and `1.0`.
- Newly evaluated active scales, in order: `0.25` and `0.5`.

For every seed, sample the exact signed 32-dimensional base-noise tensor, scale
only dimensions 0-5, and leave dimensions 6-31 unchanged. No other factor may
change.

## Metrics And Routing

Record five chunks/hashes, worst-seed maximum, aggregate mean, and raw spread.
Recompute inherited endpoint metrics from signed chunks.

- A passing new scale routes only a separately reviewed Gate C reproduction;
  prefer the largest passing scale.
- Without a pass, select the lowest-worst-error condition, then lowest mean,
  then largest active scale.
- A new interior optimum routes a narrower active-scale refinement only if its
  margin and information gain justify another reviewed inference slice.
- Endpoint optimum routes model flow-consistency correction.

Gate B requires every decoded value within 0.05 rad. An active-noise scale is a
diagnostic factor and is not automatically an accepted policy sampler.

## One-Use Boundary

Implementation, exact spec, one-use permit, tests, same-agent review, scoped
commit, push, and remote confirmation must precede model or checkpoint tensor
access. The runner writes an immutable attempt marker before model loading.

## Prohibited Actions

No optimizer, training, mutation, post-hoc correction, new scale/seed, rollout,
Gate C, hardware, camera, serial, external compute, or Brev.

## Acceptance

Tests cover lineage, masks, endpoint inheritance, base-noise equality, metrics,
selection/route precedence, one-use semantics, non-finite values, and all
forbidden truth flags. A fresh pre-run decision must authorize exactly one
Python 3.12 local-MPS inference attempt.
