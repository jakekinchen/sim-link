# Slice Brief 159 - T20.28 Exact Training-Sampler Exposure Audit

**Date:** 2026-07-14

## Objective

Reconstruct the exact T20.17 and T20.24 official-LeRobot sampler orders and
measure nominal/recovery episode, phase, approach, and frame-zero exposure
before selecting another explanation for the T20.27 regression.

## Contract

- Run no model and no optimizer. Bind the pinned `EpisodeAwareSampler` source,
  both dataset episode boundaries, training seeds, update counts, batch size,
  world size, no-resume state, and source phase records.
- Reconstruct the first 250 clean and first 500 recovery-campaign sampler
  positions with the actual pinned sampler implementation.
- Report unique sampled indices, per-episode/source/phase counts, approach and
  frame-zero exposure, and coverage fractions. Preserve nominal and recovery
  source classes separately.
- Compare early-phase exposure without claiming that count alone proves an
  optimizer effect. Select or reject the narrow exposure hypothesis.
- Do not access hardware or cameras, apply an action, run inference/training,
  start external compute or Brev, change the twin, or consume Robo Scan evidence.

## Acceptance Criteria

- Tests reject sampler source/seed/update/boundary substitution, duplicate or
  out-of-range indices, phase/source mismatches, non-finite counts, signed
  mutation, and authority escalation.
- A signed audit exactly accounts for 250 and 500 sampler positions and binds
  every position to one source episode/frame/phase.
- The result states whether T20.24 early-phase exposure was lower than T20.17
  and selects the next diagnostic without authorizing training.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commits, and
  remote branch agree before T20.28 is described as verified.

## Out Of Scope

Model inference; rollout; optimizer training; checkpoint/dataset/statistics
changes; causal attribution from counts alone; policy acceptance; physical
canary; hardware/camera access; twin calibration; Robo Scan; external compute;
or Brev.
