# Reviewer Decision 144 - T18.1 Episode-First Window Sampling

**Date:** 2026-07-13

## Decision

`CONTINUE`

## Evidence Reviewed

- Brief 116; implementation `ce3a12c`; the signed T18.1 selection manifest;
  and Session 148.
- Four focused sampling tests, the 83-test relevant regression set, and the
  byte-identical writer replay.

## Findings

- The selection has 24 valid source/task-phase/control-mode/horizon buckets.
  Each has all eight realized episodes and exactly one deterministic selected
  window per episode: 192 unique selections, no quota padding, reuse, or
  cross-episode substitution.
- T17.5b compiler/window and T17.7 audit bindings are verified. Ineligible,
  quarantined, phase-spanning, discontinuous, timestamp-drifting, and
  boundary-crossing windows fail closed before selection.
- The sampling cycle is logical only. No source/cycle buffer was persisted or
  mutated; no mixture is frozen. Training, model inference, optimizer, raw
  rewrite, physical actuation, external compute, and Brev remain closed or
  false.

## Routing

T18.1 is verified. T18.2 is next and owns append-only logical source/cycle
buffer preservation; this result does not authorize training.

## Manager / Human Escalation

None. The central training lock remains closed.
