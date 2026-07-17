# Reviewer Decision 323 - Verify F0b Owner-Authority Attribution Correction

**Date:** 2026-07-17

## Decision

`VERIFY_F0B_OWNER_ATTRIBUTION_CORRECTION_REOPEN_MODEL_FREE_MATERIALIZATION`

Correction commit `8edf1687168750781a257a39d9f5cace3a5e57f5` is exact on
origin. It supersedes only the prospective F0b owner-grant attribution in
Reviewer 322's otherwise-valid implementation boundary. No authority artifact,
renderer smoke, checkpoint read, model action, attempt marker, or rollout was
created before this correction.

## Corrected boundary

- The owner authorization source is now the direct chat instruction
  `owner_direct_chat_eight_hour_continue_authorization_2026_07_17`, with the
  exact recorded statement: "Okay. I authorize all of this for the next eight
  hours."
- `docs/autonomous-workflow/owner-direction-2026-07-17-final-overnight.md`
  remains separately labeled and bound as the task-ordering source. It is not
  represented as task-local authority.
- The owner-grant verifier deterministically reconstructs both fields and
  rejects substitution or conflation.
- The regenerated signed spec identity is
  `ddf71cf91bcfcd4a1d40573a4ce5cfd648ee9dc141b3b6186bfbbd5fc16184ce`;
  its file SHA-256 is
  `3513a75aa201275e121a3c1fbe120c3f671104513c75fc65c41c726ff8d3a53b`.
  It now content-binds the task-ordering document as a separate source.

## Verification and authority disposition

The 15-test focused F0b suite, Python compilation, offline Ruff, canonical spec
rebuild, JSON, and whitespace checks pass. The schedule, checkpoint, source,
runtime, trace, gate, terminal, and no-training semantics reviewed by Reviewer
322 are unchanged.

After this correction closeout is exact on origin, model-free authority
materialization may resume: one retained-comparator renderer smoke and the
signed owner/central/runtime/permit bundle. Pre-run acceptance, attempt-marker
creation, checkpoint tensor read, model construction/loading, inference,
simulation rollout, Gate C execution, and policy-result rendering remain
closed. Optimizer/training, retry, F1/Brev, hardware, transfer, promotion,
destructive operations, and the freeze tag remain closed.
