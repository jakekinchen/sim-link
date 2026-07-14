# Slice Brief 133 - T20.13 Dataset-Bound PI0.5 Normalizer

**Date:** 2026-07-14

## Objective

Derive a deterministic train-only PI0.5 state/action mean/std normalizer for
the T20.1 simulation dataset and prove its held-out and inverse-transform
behavior before any optimizer run.

## Contract

- Re-hash the exact T20.1 tensor view and T20.12 diagnosis. Fit state and
  action statistics only from the 488 training frames after canonical LeRobot
  conversion; held-out frames are evaluation-only.
- Use the implemented PI0.5 `MEAN_STD` formula and epsilon without clipping,
  loss reweighting, action reordering, or checkpoint mutation.
- Report every train/held-out joint's native range, fitted mean/std,
  normalized mean/std/range, inverse error, and comparison to the pinned
  checkpoint normalizer's target-scale proxy.
- Bind the exact processor construction source that will consume the frozen
  statistics in a later optimizer slice, but do not load a model or train.

## Acceptance Criteria

- Train-fitted state/action normalized means are zero and standard deviations
  are one within explicit measured tolerances; every fitted standard deviation
  is finite and above the declared minimum.
- All 732 action and 732 state rows inverse-transform within an explicit
  native-unit threshold, with measured-versus-threshold margins.
- The artifact proves no held-out value contributed to fitted statistics and
  reports held-out behavior separately without clipping or relabeling it as
  training support.
- Tests reject held-out leakage, source substitution, joint reordering,
  non-finite or near-zero statistics, false inverse claims, loss reweighting,
  and authority escalation.
- Same-agent review checks population-versus-sample standard deviation,
  epsilon asymmetry, state/action unit aliases, and unsupported causal claims.

## Out Of Scope

Optimizer training, checkpoint mutation, policy inference or acceptance,
hardware, physical transfer, promotion, external compute, and Brev.
