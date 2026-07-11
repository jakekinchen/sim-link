# Manager Intervention 010 - Bind Embedded CAD Priors Before Ready Proof

**Date:** 2026-07-10

## Decision

`STRENGTHEN T16.4 THEN CONTINUE`

## Evidence

Commit `3edc793` correctly keeps the real arm blocked and verifies its top-level
dependency-lock, TwinProfile, structural-diff, and intake references. An
independent re-signed tamper test found that nested evidence is not equivalently
bound:

- changing a CAD prior's source path or source hash was accepted;
- changing its source mass to `99` kg was accepted;
- changing its body-to-assembly transform was accepted;
- the forged intake compiled and verified with a CAD prior summary of
  `99.485006` kg;
- appending a duplicate component record was accepted.

The semantic signature proves only that a payload is internally signed. It does
not prove that nested evidence still matches repo state.

## Resolution Required

- For the default `awaiting_measurements` artifact, compare the full normalized
  intake to a deterministic rebuild from the pinned runtime MJCF and current
  bound artifacts, or equivalently validate every nested prior field against
  that rebuild.
- Reject duplicate component IDs as well as duplicate atom/prior IDs.
- Add direct re-signed tamper tests for embedded source path, file hash, source
  mass, COM/inertia, transform, and duplicate components.
- Keep output compilation dependent on the strengthened intake verifier so a
  forged CAD summary cannot propagate.
- Then complete the synthetic ready compiler and all coverage/math gates from
  brief 025.

Brief 025 is superseded by brief 026. T16.4 remains `in_progress`; training and
physical qualification remain closed.
