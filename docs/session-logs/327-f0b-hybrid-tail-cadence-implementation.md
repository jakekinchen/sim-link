# Session 327 - F0b Hybrid Tail-Cadence Implementation

**Date:** 2026-07-17

**Task:** F0b / Brief 232

**Reviewer:** 322

## Outcome

F0b's no-training hybrid-cadence evaluator is implemented and verified at
commit `1b23f6bc372e66ce5c0982d0da97d7a9fe8c1275` on origin. Signed spec
`00d7c7f300e2b8536e0a24437fadd7bf946c3580fa5eef6bfc0e632d0479953f`
binds the retained update-10,000 ACT checkpoint, exact seed-0 source episode,
original chunk-50 comparator, runtime and dependency revisions, scene assets,
strict-v2 evaluator, renderer chain, evidence contracts, and one-use/no-retry
boundary.

The schedule keeps chunk-50 execution through frame 175, records and discards
the 24 remaining frame-150 predictions at frame 176, then decodes every ten
executed actions through starts 176, 186, 196, 206, 216, 226, and 236. The
final chunk executes eight actions and retains two unexecuted selected actions.
The actor sees only current camera images and qpos. Full decoded chunks,
observed physics frames, discarded/unexecuted rows, exact comparisons,
independent strict-v2 replay, terminal evidence, and signed mirror linkage are
mandatory whether the future rollout passes or fails.

## Verification

- final spec reconstruction reproduces `00d7c7f3...` without tensor
  deserialization;
- 15 focused F0b tests pass;
- 72 relevant unittest regressions pass, including focused coverage;
- 14 T20.43c continuation/replacement pytest regressions pass under an offline
  cached pytest tool using the pinned Python 3.12 interpreter;
- Python compile, offline Ruff, JSON, path/symlink, authority, non-finite, and
  whitespace checks pass;
- same-agent adversarial review closed exact-source renderer routing, distinct
  central evidence references, root-relative retention hashing, post-marker
  exception coverage, and output-parent alias rejection before commit;
- HEAD, upstream, and the remote branch all equal `1b23f6b...` before this
  closeout.

No checkpoint tensor, model, inference, rollout, or live rendering action ran.
No optimizer, training, dataset/statistics mutation, network, package install,
external compute, Brev, hardware, camera, serial, physical motion, transfer,
promotion, destructive operation, or freeze tag was used.

## Disposition

Reviewer 322 opens only F0b model-free authority materialization after this
closeout reaches origin. That slice may render the retained comparator once as
a fresh smoke and write the signed owner/central/runtime/permit bundle. A
separate reviewed pre-run acceptance is still mandatory before the one-use
marker or any checkpoint/model/inference/simulation action. Training, retry,
F1/Brev, hardware, physical transfer, promotion, and freeze remain closed.
