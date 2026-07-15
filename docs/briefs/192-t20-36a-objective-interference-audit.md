# Brief 192 - T20.36a Objective Interference Audit

## Objective

Explain why T20.36 improved its declared joint-weighted correction objective
while losing the unchanged physical-radian Gate B action constraint, using
only existing signed T20.35x and T20.36 evidence.

## Frozen Inputs

- T20.35x signed result `e79dacff...`, run `b5cc16ef...`, and checkpoint
  identity `40c94f66...`.
- T20.36 signed result `02b543be...`, run `88daae0d...`, result file SHA-256
  `7927aaaf...`, and remotely preserved result commit `3e1f2bd`.
- The recorded 500-element standard, weighted-correction, total-objective, and
  pre-clip gradient-norm histories from the content-addressed T20.36 run.
- The unchanged 0.10 standard-objective ratio and 0.05-rad decoded-action
  thresholds. Threshold calibration or amendment is outside this slice.

## Method

Create a deterministic, signed audit that verifies all frozen identities and
quantifies source-to-campaign changes in standard objective, weighted and raw
correction objectives, decoded-action maxima, and fixed windows of the
per-update histories. Classify only what those recorded values prove:

1. weighted-objective/physical-gate aliasing when the weighted correction
   improves while raw correction and decoded-action retention worsen;
2. broad optimization regression when both weighted and raw correction worsen;
3. insufficient evidence when neither predicate is mechanically satisfied.

The audit may route the next design question. It may not prescribe or execute
an optimizer coefficient, retry, threshold change, or policy replacement.

## Acceptance

- Deterministic tests reject stale identities, missing/non-finite histories,
  wrong history length, changed thresholds, inconsistent decoded-action rows,
  and ambiguous classification.
- One signed JSON artifact records exact input hashes, source/campaign ratios,
  five decoded rows, history-window summaries, classification, and explicitly
  withheld authorities.
- Focused tests, relevant workflow checks, same-agent adversarial review,
  scoped commit, push, and remote confirmation agree.

## Prohibited Actions

No checkpoint tensor read, model construction, inference, optimizer, training,
rollout, dataset/statistics mutation, Gate B amendment, second T20.36 attempt,
policy acceptance, hardware, camera, serial, external compute, or Brev.
