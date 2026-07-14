# Session Log 192 - T20.28 Sampler Exposure Audit

## Scope

Brief 159 reconstructed exact official-LeRobot sampler positions for T20.17 and
T20.24. No model inference, rollout, action application, optimizer, hardware,
camera, external compute, or Brev was used.

## Evidence

- Audit identity:
  `2445c5d0711ebd29d6f6c92ca637b80e9c6d3e6725e39d7b427eb3b215937d38`.
- Clean: 250/250 unique positions from 1,464 frames.
- Recovery campaign: 500/500 unique positions from 2,330 frames.
- Recovery source split: 314 nominal / 186 recovery.
- Clean early phase: 14 approach / 0 frame zero.
- Recovery early phase: 26 approach / 3 frame zero.
- Recovery approach split: 21 nominal / 5 recovery.
- Recovery frame-zero split: 2 nominal / 1 recovery.

The pinned sampler is seed/epoch deterministic, non-resumed, batch size one,
and world size one. All positions bind to exact source/phase records.

## Result And Validation

T20.24 had more early-phase exposure than T20.17, so the low-exposure
hypothesis is rejected. Counts alone do not establish optimizer causality. The
next diagnostic is dataset quantile/postprocessor shift caused by the recovery
mixture.

Eighty-three relevant tests passed. Same-agent review covered sampler source,
seed, boundaries, counts, duplicates/range, phase/source classification,
signed mutation, authority, and cleanup.
