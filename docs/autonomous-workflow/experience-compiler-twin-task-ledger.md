# Experience Compiler And Hardware Twin Task Ledger

Updated: 2026-07-10

```text
training_lock: closed
current_milestone: M16 Twin and dependency foundation
current_task: T16.1 pin dependency and structural-model identities
completed: T16.0 scoped dirty-path goal-loop guard; prior evidence retained
evidence: 70 tests; 51 protected paths unchanged across pair dry-run; commit b5d056b
remaining: M16-M19 prerequisites, then Gates C-D and closeout
blockers: physical M19 work requires separate read and motion authority; offline work is unblocked
next_step: emit and validate one tracked dependency lock with upstream and local patch identities
```

## Rules

- Update this ledger at task start and after every verification boundary.
- Commit feature, compiler-run, training, and evaluation boundaries separately.
- Raw rollout bytes are append-only and never reinterpreted without a new compiled view.
- `recovery` is a control mode, never a task phase.
- Unknown coordinate, owner, prompt, or temporal semantics are quarantined.
- No M20-M22 task may start while `training_lock` is `closed`.
- Physical census, motion, or contact tasks require explicit owner authorization.
- States are `pending`, `in_progress`, `verified`, `blocked`, `deferred`, and `superseded`.

## M16 - Twin And Dependency Foundation

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T16.0 | verified | none | Add a scoped dirty-path guard, freeze rungs 500/1,000, and validate the repo goal-loop launch | 70 tests; 51 protected paths unchanged across pair dry-run; b5d056b |
| T16.1 | in_progress | T16.0 | Pin LeRobot, OpenPI reference, Menagerie/Robot Studio SO-101, licenses, and local patches | Tracked dependency lock resolves every runtime input to SHA/hash |
| T16.2 | pending | T16.1 | Define TwinProfile, TwinQualificationSpec, and TwinQualificationReport schemas | Property/schema tests; content-addressed simulation-only example |
| T16.3 | pending | T16.1-T16.2 | Reconcile current Robot Studio MJCF with pinned Menagerie rather than replacing it silently | Machine structural diff of inertials, limits, contacts, camera, gripper, actuator, backlash |
| T16.4 | pending | T16.2-T16.3 | Add measured-part mass intake and assembly inertia/COM compiler | Parallel-axis golden tests; ambiguous/missing weights fail closed |
| T16.5 | pending | T16.2-T16.4 | Build fake-bus/recorded-trace identification and qualification harness | Offline census, fitting, qualification, and no-hardware safety tests |

## M17 / Gate A - Truthful Experience Compiler

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T17.1 | pending | T16.2 | Define immutable raw rollout/frame records and provenance dictionaries | Schema includes rollout/segment IDs, timestamps, prompt, orthogonal semantics, action variants, reward/progress provenance |
| T17.2 | pending | T16.2-T16.3, T17.1 | Implement a named canonical SO-101 processor shared by collection, training, evaluation, and adapters | Permutation, randomized round-trip, bounds, action-mode, gripper-monotonicity, golden-pose tests |
| T17.3 | pending | T17.2 | Generate immutable `normalization_bundle.json` | Feature order, algorithm, coordinates, cameras, tokenizer, processors, dependency SHAs pinned |
| T17.4 | pending | T17.1-T17.3 | Compile `frames.parquet` and hard-boundary `segments.parquet` | Raw hashes retained; owner/reset/prompt/contract/gap changes split or fail |
| T17.5 | pending | T17.2-T17.4 | Compile unpadded `window_index.parquet` for horizons 5/10/15/50 | No gaps, missing actions, padding, reset, teleport, drift, or forbidden transition |
| T17.6 | pending | T17.1-T17.5 | Recompile qualifying legacy raw rollouts and quarantine ambiguous legacy data | No guessed migration; reasoned quarantine manifest |
| T17.7 | pending | T17.1-T17.6 | Add full compiler manifest and deterministic 100-window replay/annotation audit | Zero invalid accepted windows; collection/training/inference tensor parity |

## M18 / Gate B - Intentional Mixture And Corrections

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T18.1 | pending | M17 | Sample valid windows episode-first over source x task-phase x control-mode | Deterministic configured/realized counts, unique ratio, episodes/cycles, seed, index hash |
| T18.2 | pending | T17.1, T17.7 | Preserve append-only cycle/source logical buffers | Earlier cycles immutable; mutation and duplicate rejection retained |
| T18.3 | pending | T17.1, T17.4 | Compile exact-state phase, progress, reward components, and provenance | Deterministic predicates; privileged fields excluded from actor inputs |
| T18.4 | pending | T16.3, T17.1-T17.5, T18.3 | Implement snapshot branch-and-correct linked by `correction_event_id` | Restored snapshots match; failure and correction remain immutable branches |
| T18.5 | pending | T18.1-T18.4 | Generate `dataset_mixture_manifest.json` and training-input manifest | Re-run produces identical selected window IDs and composition |

## M19 - Physical Hardware Twin Qualification

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T19.1 | pending | M16, read authority | Run read-only servo/firmware/register census | Immutable hardware snapshot; no writes or motion |
| T19.2 | pending | T19.1, motion authority | Calibrate cameras, joint offsets, kinematics, timing, and gripper aperture | Held-out reprojection, pose, and timing tolerances |
| T19.3 | pending | T19.1-T19.2, motion authority | Identify delay, saturation, settling, directionality, backlash, friction, compliance | Per-joint fitted distributions and held-out trajectory evidence |
| T19.4 | pending | T19.2-T19.3, contact authority | Identify fingertip/table friction, slip, force/current, and object profiles | Held-out grasp/lift/slip/release envelope |
| T19.5 | pending | T16.4, T19.2-T19.4 | Fit posterior and run held-out qualification | Every TwinQualificationSpec metric passes or is explicitly failed |
| T19.6 | pending | T19.5, M17 | Bind qualified twin hash and requalification triggers to all downstream artifacts | Contract/hardware drift blocks execution |

## M20 / Gate C - Cheap Falsification And Clean Supervision

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T20.1 | pending | M17-M19 | Freeze one clean single-cube dataset, split, twin, prompts, and seeds | Immutable train/evaluation specification |
| T20.2 | pending | T20.1 | Overfit one to three episodes with ACT | Near-zero train error plus closed-loop behavior change |
| T20.3 | pending | T20.1 | Repeat tiny overfit with PI0.5 | Same falsification evidence and physical semantics |
| T20.4 | pending | T20.2-T20.3 | Add explicit accumulation and run 250/500/1,000 optimizer-update MPS ladder | Updates distinct from microbatches; finite gradients; exact sample audit |
| T20.5 | pending | T20.4 | Sweep PI0.5 execution horizons 5/10/15 with chunk size 50 | Same weights/seeds; queue resets and open-loop duration recorded |
| T20.6 | pending | T20.2-T20.5 | Run fixed one-cube phase-level evaluation | Approach through stable post-release and retreat metrics |
| T20.7 | pending | T20.1, T20.6 | Bake off PI0.5, SmolVLA, ACT, and Diffusion Policy | Same semantics, splits, samples seen, seeds, and proof modes |
| T20.8 | pending | T20.6-T20.7 | Promote or reject | Stable nonzero strict success; locked audit remains one-use |

## M21 / Gate D - Improve A Competent Policy

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T21.1 | pending | M20 | Emit exact-state SARM-compatible progress data | Hashed progress artifact and predicate validation |
| T21.2 | pending | T21.1 | Compare uniform BC, balanced BC, and balanced exact-progress RA-BC | Paired ablation on identical seeds |
| T21.3 | pending | T21.2 | Add residual-RL readiness gate | Blocks without repeatable strict success and deployment-honest actor inputs |
| T21.4 | pending | T21.3 | Adapt EXPO-style learner/client interfaces | Frozen base, bounded residual, privileged critic allowed, actor privilege rejected |
| T21.5 | pending | T21.4 | Run bounded residual-RL experiment | Budget/safety logs and paired accept/reject evaluation |
| T21.6 | pending | T21.2-T21.5 | Add one-factor curriculum over the qualified posterior | Competence-gated levels and untouched realism holdout |
| T21.7 | pending | T21.5-T21.6 | Final promotion/rollback decision | Accepted-pointer integrity and proof matrix |

## M22 - Physical Shadow And Closeout

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T22.1 | pending | M19, M21 | Run explicitly authorized read-only observation/tensor parity in shadow mode | Real versus compiled tensors; no actuation |
| T22.2 | pending | T22.1, motion authority | Review commands, then validate one low-risk phase at reduced speed | Deadman/workspace limits and physical evidence |
| T22.3 | pending | T22.2 | Produce final sim-to-real capability audit | Honest proof matrix and remaining gates |

## Existing Work Disposition

- M0-M9 safety, Git, cleanup, evaluation, promotion, and rollback contracts remain valid.
- T10.1-T10.5 are legacy-v1 precursors superseded for new training by T17.1-T17.7.
- T11.1 is superseded by valid-window T18.1; T11.3 remains a useful trigger primitive.
- T11.4 hash/duplicate checks remain useful but its registry is superseded by T18.2.
- T12.1-T12.5 remain valid and will be reused by M20-M21.
- T13.1's 250 rung remains pipeline/development evidence; later rungs move to T20.4.
- T13.2-T13.4 move to T20.5, T20.7, and T20.8.
- M14-M15 move to M21-M22.

## Milestone Log

### 2026-07-10 - Advice rebaseline

```text
Current task: T16.0
State: in_progress
Completed: converted the new architecture into prerequisite-gated execution order
Evidence: local MJCF has CAD inertials/STS prior; 3,327 H50 windows cross minimal semantic boundaries in the current corpus
Commit: pending
Remaining: M16-M19 before any more training
Blockers: none for offline implementation
Training lock: closed
Next step: protect and dry-run the repo-local goal loop, then pin dependencies and reconcile the twin
```

### 2026-07-10 - T16.0 scoped goal-loop guard

```text
Current task: T16.1
State: in_progress
Completed: protected-worktree snapshot/verify and scoped pair/start/stop wrappers
Evidence: 70 tests; 51 protected paths; pre/post dry-run guard pass
Commit: b5d056b
Remaining: dependency lock and twin foundation
Blockers: none for offline work
Training lock: closed
Next step: pin all policy/model/runtime repositories and local patches
```
