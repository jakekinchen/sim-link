# Reviewer Decision 322 - Verify F0b Hybrid Tail-Cadence Implementation

**Date:** 2026-07-17

## Decision

`VERIFY_F0B_IMPLEMENTATION_OPEN_MODEL_FREE_AUTHORITY_MATERIALIZATION`

Brief 232's implementation boundary is verified at commit
`1b23f6bc372e66ce5c0982d0da97d7a9fe8c1275` on origin. The signed F0b spec
has identity
`00d7c7f300e2b8536e0a24437fadd7bf946c3580fa5eef6bfc0e632d0479953f`
and file SHA-256
`d699d451487ad6dc1ef3fc1e8fc61125a3ab0809a902df7fa03c927aacb460a1`.
It grants no checkpoint tensor read, model construction, inference, optimizer,
simulation rollout, Gate C verdict, physical authority, or retry.

## Verified contract

- The one retained update-10,000 ACT checkpoint is bound as an exact two-file
  tree with identity `c77ee36...`; its configuration remains chunk size 50,
  `n_action_steps=50`, device MPS, and no tensor was deserialized during this
  review.
- The sole schedule is decode starts
  `[0,50,100,150,176,186,196,206,216,226,236]`, executed lengths
  `[50,50,50,26,10,10,10,10,10,10,8]`, one frame-176 queue reset with 24
  discarded actions, and two selected-but-unexecuted terminal actions.
- Actor input is limited to the two current RGB images and six current qpos
  values. Phase, progress, velocity, timestamps, source actions, scripted
  actions, and source fallback do not enter the decoder.
- Every successful attempt must retain all eleven 50x6 decoded chunks, all 244
  observed physics frames, the exact discarded and terminal suffixes, source
  comparisons, independently replayed strict-v2 gates, a replayable tracked
  trace, and a signed MP4 manifest.
- The exact LeRobot and SO-ARM checkout revisions, relevant ACT/processor and
  evaluator/renderer source bytes, the 33-file SO-101 asset tree, R0
  statistics/retention, F0a, R2, comparator trace, and exact seed-0 source
  episode are content-bound. Unrelated dirt inside external checkouts is not
  claimed clean and is not part of this implementation commit.
- The renderer dispatch preserves legacy schemas, verifies F0b traces locally,
  and routes F0b to the exact hash-bound seed-0 source episode rather than
  first-match discovery.

## Adversarial review

Schedule drift, missing/extra resets, 23- or 25-action discards, non-finite
chunks, hidden actor inputs, forged strict-v2 success, resigned source or
checkpoint drift, symlinked output parents, success/failure coexistence,
optimizer or dataset-loader calls, owner escalation, and central-smoke
escalation all fail closed in deterministic tests. The one-use marker precedes
every checkpoint/model action, and every exception after the marker routes to
a terminal infrastructure receipt with retry false.

The central composer grants only its existing
`simulation_training_ready` prerequisite from distinct owner, spec, renderer
smoke, R0 statistics, R0 retention, and R2 result evidence. The task-local
permit narrows that prerequisite to one evaluation and explicitly denies
optimizer creation and training; it is not a training-lock transition.

No checkpoint tensor was read, no model was constructed or loaded, no policy
inference or simulation rollout ran, no new renderer smoke ran, and no
optimizer, dataset/statistics mutation, network, external compute, Brev,
hardware, camera, serial, physical motion, transfer, promotion, destructive
operation, or freeze-tag action occurred during implementation or review.

## Verification evidence

- final model-free spec write and independent rebuild: pass, identity
  `00d7c7f3...`;
- focused F0b suite: 15 pass;
- relevant ACT, artifact, authority, strict-v2, and renderer unittest suite:
  72 pass including F0b;
- T20.43c continuation/replacement pytest suite: 14 pass;
- Python compile, offline Ruff, JSON parse, non-finite/path/symlink checks, and
  whitespace checks: pass;
- implementation commit, upstream, and `ls-remote` origin branch: exact match.

The pinned future runner intentionally has no pytest package. The 14
pytest-style regressions ran from an offline cached pytest tool under that same
Python 3.12 interpreter and emitted only two unknown-asyncio-config warnings.
No repo dependency or lockfile changed.

## Authority disposition

F0b remains in progress. After this reviewer closeout is exact on origin, the
next allowed slice is model-free authority materialization only: one fresh
retained-trace renderer smoke plus signed owner, central request/decision,
runtime preflight, and one-use permit artifacts. Checkpoint tensor read, model
construction/loading, policy inference, attempt-marker creation, simulation
rollout, Gate C execution, and policy-result rendering remain closed until a
separate pre-run acceptance is reviewed, committed, pushed, and exact on
origin. Optimizer/training, retry, F1/Brev, hardware, transfer, promotion,
destructive operations, and the freeze tag remain closed.
