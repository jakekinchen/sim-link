# Reviewer Decision 143 - T17.7 Compiler Window Replay Audit

**Date:** 2026-07-13

## Decision

`CONTINUE`

## Evidence Reviewed

- Brief 115; implementation commits `435ecd9` and `c1f0a40`; the signed
  100-window replay audit; and Session 147.
- Five focused audit tests, the 79-test relevant regression set, and the
  byte-identical T17.7 writer replay with unchanged source-writer verification.

## Findings

- Selection is fixed at 25 windows per horizon and covers all eight realized
  rollouts before hash-ranked remainder selection. It has no sample padding,
  duplicate reuse, horizon skew, or silent source expansion.
- Each selected window is bound through raw frame record identity, compiler row,
  segment, and index row. Internal boundary crossing, non-contiguity,
  timestamp drift, incomplete actions, actor-input leakage, image hash drift,
  and rollout-identity mismatch fail closed.
- Collection/training/inference parity is explicitly limited to canonical shared
  input descriptors. Requested actions remain separate target descriptors. No
  model was loaded or called, and this audit does not evidence trained-policy
  behavior.
- M17 is complete. Training, optimizer, model inference, physical actuation,
  raw rewrite, external compute, and Brev authority remain closed or false.

## Routing

T18.1 is next: deterministic episode-first sampling of the verified M17 windows.
This T17.7 result provides source integrity only and must not be used to open
the central training lock.

## Manager / Human Escalation

None. The training lock remains closed and physical work still needs separate
owner permits.
