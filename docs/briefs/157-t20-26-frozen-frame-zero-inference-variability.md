# Slice Brief 157 - T20.26 Frozen Frame-Zero Inference Variability

**Date:** 2026-07-14

## Objective

Quantify within-process and cross-process action variability for the immutable
T20.17 and T20.24 PI0.5 adapters on one exact held-out frame-zero observation
before attributing T20.25 differences to training.

## Contract

- Run no optimizer and mutate no checkpoint. Reverify both training summaries,
  checkpoint trees, adapters, source seed-6 episode, and T20.25 gate.
- For each candidate, launch two independent local-MPS processes. In each
  process, reconstruct the exact seed-6 frame-zero simulator observation and
  call the frozen adapter after a reset under a fixed declared seed schedule.
- Capture repeated same-seed samples and distinct-seed samples without applying
  any action or completing a rollout. Bind every finite six-joint requested
  action to the source observation, checkpoint, runtime stack, process batch,
  and inference seed.
- Measure same-process same-seed equality, cross-process same-seed differences,
  and distinct-seed dispersion per joint and aggregate. Do not conflate
  stochastic sampling variability with training effect or closed-loop drift.
- Select the smallest next corrective or diagnostic step from measured facts.
  Do not allocate optimizer work or accept either policy.
- Do not access hardware or cameras, instantiate a physical robot, start
  external compute or Brev, change the twin, or consume Robo Scan evidence.

## Acceptance Criteria

- Tests reject missing/reordered candidates, batches, samples, seeds, or joints;
  observation/source/checkpoint substitution; non-finite action values; hidden
  action application; signed mutation; and authority escalation.
- Four independent candidate/batch artifacts each bind one identical source
  observation and a fixed same-seed/distinct-seed schedule.
- A signed gate reports within-process repeat error, cross-process repeat error,
  distinct-seed dispersion, and whether the T20.25 reproducibility gap is
  reproduced at frame zero.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commits, and
  remote branch agree before T20.26 is described as verified.

## Out Of Scope

Closed-loop rollout; optimizer training; checkpoint/dataset/statistics changes;
policy ranking or acceptance; physical canary; hardware/camera access; twin
calibration; Robo Scan; external compute; or Brev.
