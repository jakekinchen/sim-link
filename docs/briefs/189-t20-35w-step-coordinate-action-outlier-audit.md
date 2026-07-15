# Brief 189 - T20.35w Step/Coordinate Action-Outlier Audit

## Objective

Determine whether T20.35t's remaining 0.05-rad action failures are sparse in
action time and joint coordinate or distributed across the 50-by-6 decoded
chunks, using only signed T20.35v trajectories and immutable target evidence.

## Frozen Sources

- Bind T20.35v result `aad8a148...`, attempt `30df1e26...`, spec/permit/runtime
  identities, and all five exact decoded chunks.
- Reuse the exact 50-by-6 dataset target from the signed T20.35o/Q lineage and
  the normalized 50-by-32 target for final-state comparisons.
- Preserve the 0.05-rad action threshold and active/padded dimension meanings.

## Audit Contract

Without loading a model or checkpoint, recompute every seed/action-index/joint
absolute error. Report per-seed and aggregate exceedance counts, maximum and
mean errors by action index and joint, concentration of squared error mass,
the exact worst cells, and corresponding last-captured time-0.1 normalized-state
residuals.
Classify the failure as sparse time/coordinate outliers, joint-dominant,
time-band-dominant, or distributed using explicit signed thresholds. Route at
most one smallest simulation-only correction hypothesis.

## Prohibited Actions

No model load, checkpoint access, inference, optimizer creation/training,
source/result mutation, retry, extra seed/state/time, sampler or processor
change, rollout, Gate C, hardware, camera, serial, external compute, or Brev.

## Acceptance

Every decoded endpoint and target hash verifies; all 1,500 action errors and
all derived summaries recompute exactly and remain finite; and one signed audit
routes the next smallest discriminator without claiming Gate B, Gate C, policy
acceptance, or physical readiness.

## Result

Signed audit `e52d6d08...`, preserved at `99cbbc4`, recomputes all 1,500
seed/action/joint errors. Exactly 370 cells exceed 0.05 rad. Shoulder lift
carries `50.6574%` of physical-radian squared error and wrist roll `29.3595%`,
while no joint exceeds `20.7126%` of last-captured normalized-state error mass.
The first ten actions carry `42.1972%`, below the 50% time-band threshold; the
failure is neither sparse nor time-band dominant. Reviewer 236 routes one
physical-gate-aligned joint-weighted correction design with standard replay.
Gate B and Gate C remain closed. No model, checkpoint, inference, optimizer,
rollout, hardware, external compute, or Brev action occurred.
