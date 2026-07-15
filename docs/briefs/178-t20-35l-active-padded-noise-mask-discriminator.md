# Brief 178 - T20.35l Active-Versus-Padded Noise-Mask Discriminator

## Objective

Determine whether T20.35j's initial-noise effect is driven primarily by the six
active robot-action dimensions, the 26 padded dimensions exposed by T20.35k, or
both. Change only which dimensions retain the same signed base-noise tensor.

## Frozen Sources And Conditions

- T20.35j result `e9bbff84...` and T20.35k audit `bc9f0845...`.
- Exact expert-only checkpoint, one batch/target, processors, five seeds,
  standard-normal base tensors, 10 inference steps, and 0.05-rad action gate.
- Signed inherited endpoints: `active_normal_padded_normal` and
  `active_zero_padded_zero` from T20.35j.
- New condition 1: `active_normal_padded_zero`.
- New condition 2: `active_zero_padded_normal`.

The first six dimensions are active and dimensions 6-31 are padded. Each new
condition must use the same per-seed base-noise hash as the inherited endpoints.
No additional scale, seed, cadence, checkpoint, target, or correction is
allowed.

## Metrics And Routing

Record five decoded chunks/hashes, worst-seed maximum error, aggregate mean,
and raw cross-seed spread for each new condition. Recompute inherited endpoint
metrics from their signed chunks.

- Any Gate B pass routes only a separately reviewed Gate C reproduction.
- A positive active-normal/padded-zero result isolates padded-noise sensitivity.
- A positive active-zero/padded-normal result isolates active-prior sensitivity.
- Two positive mixed masks route a joint flow-robustness audit.
- Neither positive routes general model robustness correction.

Positive means all three metrics strictly improve over all-normal. A Gate B
pass still requires every decoded value within 0.05 rad.

## One-Use Boundary

Implementation, exact spec, one-use permit, tests, same-agent review, scoped
commit, push, and remote confirmation must precede model or checkpoint tensor
access. The runner writes an immutable attempt marker before model loading.

## Prohibited Actions

No optimizer, training, checkpoint/dataset/source mutation, post-hoc action
correction, new endpoints, rollout, Gate C, hardware, camera, serial, external
compute, or Brev. A mixed-mask result is diagnostic and cannot itself accept a
policy.

## Acceptance

Tests cover exact lineage, dimension masks, base-noise equality, inherited
endpoint replay, metrics, route precedence, one-use semantics, non-finite
values, and every forbidden truth flag. A fresh pre-run reviewer decision must
authorize exactly one Python 3.12 local-MPS inference attempt.

## Pre-Run Boundary

Implementation `2f04395`, spec `4c346688...`, permit `5b990e78...`, and
Reviewer 216 authorize exactly one Python 3.12 local-MPS model-load/inference
attempt after remote preservation. The runner inherits both endpoint chunks,
evaluates only the two mixed masks, and validates every per-seed base-noise hash
before inference. Sixty relevant tests and 17 subtests pass; exact spec/permit
verification agrees under Python 3.11 and 3.12. No model, checkpoint tensor,
inference, optimizer, mutation, rollout, Gate C, hardware, external compute, or
Brev action occurred at this boundary.

## Result Boundary

The consumed attempt `adf33ca1...` produced result `b4fc6060...`, preserved at
`1040478`. Both mixed masks strictly improve all three metrics over all-normal;
active-zero/padded-normal is best at `0.066398` worst error, but remains above
0.05 rad. Reviewer 217 accepts joint active/padded sensitivity and routes only
the model-free T20.35m factorial interaction audit. Gate B and Gate C remain
closed.
