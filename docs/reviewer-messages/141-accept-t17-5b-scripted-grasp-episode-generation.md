# Reviewer Decision 141 - T17.5b Scripted Grasp Episode Generation

**Date:** 2026-07-13

## Decision

`CONTINUE`

## Evidence Reviewed

- Brief 112; implementation commit `5c3c34b`; evidence commit `8ccee81`; the
  signed episode-store manifest; compiler and window manifests; and Session
  145.
- 15 focused compiler/window/episode tests, the 68-test relevant regression
  set, existing T17.4/T17.5 writer verification, and the fresh full eight-seed
  byte-identical replay.

## Findings

- Eight fixed-seed scripted MuJoCo episodes are honest simulation-unassisted
  evidence, not training or physical proof. Seed 0 preserves the strict
  8/24/12/24 cycle; all eight outcomes are strict successes.
- Requested actions are observed. Proposed, projected, sent, and measured
  actions are truthfully `derived` only because this scripted simulator has no
  separate stage; each carries a named derivation, and both compiler and window
  layers require that derivation, exact six-joint order, and finite values.
- The new compiled source is non-empty without padding or boundary crossing:
  1,952 eligible frames, 88 segments, zero quarantines, and 120 horizon-50
  windows. Five 256px top/wrist keyframes provide Seed-0 grasp evidence.
- All raw bytes are append-only and ignored; tracked artifacts bind their
  content hashes. Deterministic regeneration proves no manifest/compiler/window
  drift. Training, optimizer, physical, raw-rewrite, and Brev authority remain
  false or closed.

## Routing

T17.5b is verified. T17.6 is the next pending offline task: recompile only
qualifying legacy raw rollouts and retain reasoned quarantine for ambiguity.
T17.7 remains downstream of both T17.5b and T17.6.

## Manager / Human Escalation

None. The central training lock remains closed; this result does not authorize
training, external compute, hardware access, or physical motion.
