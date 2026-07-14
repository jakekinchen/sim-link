# Reviewer Decision 139 - T17.5 Unpadded Window Index

**Date:** 2026-07-13

## Decision

`CONTINUE`

## Evidence Reviewed

- Brief 111, the source-bound compiler/writer/tests, tracked output hashes,
  canonical state and ledger updates, and Session 143.
- 6 focused tests and the 74-test relevant compiler/contract regression gate.
- Both deterministic writer `--verify` paths, pointer check, lock check, and
  diff check.

## Findings

- The zero-row result is correct: T17.4 has zero eligible segments, and T17.5
  reports zero windows at all four horizons rather than padding or inferring
  data.
- Source-manifest/hash binding, frame/segment identity, duplicate/index/gap
  rejection, internal-boundary exclusion, action finiteness, and closed
  authority flags are covered. No raw bytes, training, optimizer, hardware,
  physical actuation, Brev, or external compute was used.
- Evidence anchor 75: the adopted T17.5b proposal requires truthful `derived`
  action variants, while this verified compiler boundary accepts only
  `observed`. The next brief must implement a verifiable, fail-closed derived
  representation before recording non-empty episodes; relabeling is rejected.

## Routing

T17.5 is verified. T17.5b is the next pending task and owns the missing raw
episode generation. T17.6 remains independent; T17.7 now depends on T17.5b
because its 100-window audit requires actual windows.

## Next Action

Start Brief 112 only after the T17.5 verification commit is remotely preserved.
Implement the narrow derived-action compatibility rule first, then the
append-only scripted-grasp recorder and a fresh non-empty T17.4 compiled view.

## Manager / Human Escalation

None. Training and physical work remain separately gated.
