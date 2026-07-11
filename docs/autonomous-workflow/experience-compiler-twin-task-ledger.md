# Experience Compiler And Hardware Twin Task Ledger

Updated: 2026-07-11

```text
training_lock: closed
run_window: start 2026-07-11T02:14:07-05:00; no new major slice after 2026-07-11T11:44:07-05:00; hard closeout 2026-07-11T12:14:07-05:00
current_milestone: M16 Twin and dependency foundation
current_task: T16.5b reviewed offline harness; metadata discovery is next after remote preservation
completed: T16.0 guard; T16.1 dependency inventory; T16.1b unified executable stack; T16.2/T16.2b mechanically computed qualification; T16.2b-A central authority composition; T16.3 structural baseline; T16.4/T16.4b production measured-inertial compiler and numerical hardening; corrected T16.5a offline no-write census preflight
evidence: T16.5b harness commit 16d24ea and reviewer 050 passed 14 dedicated, 30 combined census, and 209 broad tests plus both supported offline runtime verifiers; no hardware enumerated or opened
remaining: T16.5b live read-only census; T16.5c no-actuation observation/shadow/replay; T16.6 exact initial supervised micro-motion permit
owner_authority: final operator confirmation is granted for one exact initial session-scoped supervised_micro_motion permit after T16.5a-T16.5c and every permit/lease gate pass; no second prompt is required; any expansion is unauthorized
blockers: no metadata-discovery blocker after the reviewed harness is remotely preserved; serial/camera open still fails closed on identity, calibration, lease, or contract ambiguity; physical motion waits on verified T16.5a-T16.5c plus an exact valid permit and active owner-presence lease
next_step: remotely preserve commit 16d24ea and reviewer 050, then perform metadata-only discovery with zero serial or camera opens
```

## Rules

- Update this ledger at task start and after every verification boundary.
- Commit feature, compiler-run, training, and evaluation boundaries separately.
- Raw rollout bytes are append-only and never reinterpreted without a new compiled view.
- `recovery` is a control mode, never a task phase.
- Unknown coordinate, owner, prompt, or temporal semantics are quarantined.
- No M20-M22 task may start while `training_lock` is `closed`.
- Live read-only census/camera capture is conditionally owner-authorized only
  after verified T16.5a while the owner-presence lease is active.
- The latest owner message is final confirmation for one exact initial
  no-op-equivalent then one-joint displacement-and-return permit. No second
  prompt is required, but no write or motion occurs unless the signed,
  content-addressed, session-scoped permit and every prerequisite validate.
- Any additional joint, gripper, reach, contact, task, policy actuation, or
  material permit expansion is unauthorized.
- States are `pending`, `in_progress`, `verified`, `blocked`, `deferred`, and `superseded`.

## M16 - Twin And Dependency Foundation

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T16.0 | verified | none | Add a scoped dirty-path guard, freeze rungs 500/1,000, and validate the repo goal-loop launch | 70 tests; 51 protected paths unchanged across pair dry-run; b5d056b |
| T16.1 | verified | T16.0 | Inventory LeRobot, OpenPI reference, Menagerie/Robot Studio SO-101, licenses, and local patches | Dependency inventory and source evidence verified; executable resolution completed separately by T16.1b |
| T16.1b | verified | T16.1 | Unify the executable LeRobot/preprocessing revision used by every robotics stage | `dca2b45`; stack identity `c8e903e7...`; exact base + tracked patch + environment lock + saved-sample stage parity |
| T16.2 | verified | T16.1b | Define TwinProfile, TwinQualificationSpec, and TwinQualificationReport schemas | Schema scaffold plus T16.2b computed decision path verified on fixture evidence; no physical qualification |
| T16.2b-A | verified | T16.1b,T16.2,T16.4 | Define the only central composer for global authority from scoped component capabilities | `c0b9629`; reviewer 043; contract `6d04b205...`; 101-test broad gate; remote through `e1d59ca`; grants contract validity only |
| T16.3 | verified | T16.1-T16.2 | Reconcile current Robot Studio MJCF with pinned Menagerie rather than replacing it silently | `7bebf55` baseline plus semantic corrections through `cadc0f3`; reviewer decision 033 closes the v2 identity reopen after manager intervention 008 |
| T16.4 | verified | T16.2-T16.3 | Add measured-part mass intake and assembly inertia/COM compiler | Production compiler valid on declared fixture evidence; current-arm physical input remains blocked |
| T16.4b | verified | T16.2,T16.4,T16.2b-A | Implement strict production measured-inertial intake with local capability output | `7d05629`/reviewer 045/remote `dbdd1ef`; normalized Jacobi convergence/residual checks; scale-relative adversarial coverage; 17 focused and 131 broad tests |
| T16.2b | verified | T16.1b,T16.2,T16.2b-A,T16.4b | Compute qualification results from the specification and independently verify them | `710960b`/reviewer 046/remote `383557b`; 16 focused and 147 broad tests; fixture numeric pass remains qualification-withheld |
| T16.5 | superseded | T16.1b,T16.2b,T16.4b | Original combined census task | Split by owner steering into T16.5a/T16.5b/T16.5c/T16.6 so offline, live read-only, shadow, and supervised motion proof cannot collapse |
| T16.5a | verified | T16.1b,T16.2b,T16.4b | Offline no-write transport/lifecycle preflight | Corrected `5102422`/`eeb16e1`; reviewer 049; remote `2407299`; v2 protocol-0/hash/semantic binding; 16 focused and 195 broad tests; `census_trace_conformant` only |
| T16.5b | in_progress | T16.5a | Live read-only census and synchronized observation while owner-present lease is active | `16d24ea`; reviewer 050; offline harness accepted after 14 dedicated/30 combined/209 broad tests; metadata-only discovery next after remote preservation; no live proof label yet |
| T16.5c | pending | T16.5b | Real-observation preprocessing, PI0.5 shadow, and matched MuJoCo replay with no actuation | `physical_observation_capture` and `policy_shadow`; requested policy actions never sent; replay remains simulation/replay evidence |
| T16.6 | pending | T16.5a-T16.5c | Exact initial supervised physical POC under final owner confirmation | Signed/content-addressed session permit; no-op-equivalent then at most one small one-joint delta and exact return; no second prompt; active lease; requested/projected/sent/measured separate; `supervised_micro_motion` only |

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
| T20.1 | pending | M17-M18 | Freeze one clean simulation-only single-cube dataset, split, structural twin, prompts, and seeds | Immutable train/evaluation specification with explicit `simulation_only` authority |
| T20.2 | pending | T20.1 | Overfit one to three episodes with ACT | Near-zero train error plus closed-loop behavior change |
| T20.3 | pending | T20.1 | Repeat tiny overfit with PI0.5 | Same falsification evidence and physical semantics |
| T20.4 | pending | T20.2-T20.3 | Add explicit accumulation and run 250/500/1,000 optimizer-update MPS ladder | Updates distinct from microbatches; finite gradients; exact sample audit |
| T20.5 | pending | T20.4 | Sweep PI0.5 execution horizons 5/10/15 with chunk size 50 | Same weights/seeds; queue resets and open-loop duration recorded |
| T20.6 | pending | T20.2-T20.5 | Run fixed one-cube phase-level evaluation | Approach through stable post-release and retreat metrics |
| T20.7 | pending | T20.1, T20.6 | Bake off PI0.5, SmolVLA, ACT, and Diffusion Policy | Same semantics, splits, samples seen, seeds, and proof modes |
| T20.8 | pending | T20.6-T20.7 | Accept or reject simulation policy; separately evaluate transfer eligibility | `simulation_policy_accepted` may pass under simulation authority; `physical_transfer_eligible` remains false until M19 passes |

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

### 2026-07-11 - T16.5b offline live-readonly harness locally reviewed

```text
Current task: T16.5b
State: in_progress
Completed: bounded metadata-discovery, exact identity/lease contract, no-write bus, finite camera, private evidence, and redacted manifest harness reviewed offline
Evidence: implementation 16d24ea; reviewer 050; 14 dedicated, 30 combined census, and 209 broad tests; both .mujoco_venv and external/leLab offline verifiers; Black, py_compile, static no-write inspection, and diff checks
Commit: 16d24ea; review/canonical preservation pending
Remaining: commit and remotely preserve reviewer boundary; metadata-only discovery; exact lease/contract; one bounded read-only census/camera attempt
Blockers: no offline blocker; live open fails closed on any identity, calibration, lease, camera, source, or contract ambiguity
Hardware state: not enumerated and not opened
Training lock: closed
Next step: commit reviewer 050 and canonical state, push only the named branch, confirm remote, then run metadata discovery only
```

### 2026-07-11 - Corrected T16.5a remotely verified; T16.5b reopened

```text
Current task: T16.5b
State: in_progress
Completed: corrected T16.5a v2 protocol/source binding remotely preserved with reviewer 049
Evidence: local HEAD, origin tracking, and git ls-remote all matched 240729968ee1956cab489ea49501768156b16777; commits 5102422/eeb16e1 and reviewer 049 are ancestors; unrelated dirty baseline remains 232 paths
Commit: 5102422/eeb16e1 correction; 2407299 reviewer boundary
Remaining: offline live-adapter/discovery/camera/evidence tests, lease revalidation, then one bounded live read-only attempt
Blockers: none for offline implementation; live access fails closed on lease or identity ambiguity
Training lock: closed
Next step: execute Brief 039 offline gates before opening any device
```

### 2026-07-11 - T16.5a protocol/source correction locally reviewed

```text
Current task: T16.5a
State: in_progress
Completed: corrected protocol 0; v2 source-hash contract; independent protocol/baud/model/resolution/register/joint/lifecycle semantic parser; constants derived from verified semantics
Evidence: commits 5102422/eeb16e1; reviewer 049; 16 focused and 195 broad tests; contract 73652ffa...; trace 17921a5f...; result 4a83298b...
Commit: 5102422 and eeb16e1; review/remote preservation pending
Remaining: preserve correction and reviewer on origin, then reclose T16.5a and reopen Brief 039
Blockers: no offline blocker; all live hardware remains closed
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.5a reopened before live access

```text
Current task: T16.5a
State: in_progress
Completed: contained a protocol binding defect before any hardware enumeration or open
Evidence: reviewer 048; pinned Feetech DEFAULT_PROTOCOL_VERSION=0 and MODEL_PROTOCOL[sts3215]=0; fixture declared 1; source hashes 0460413c.../71f7f7be...
Commit: correction pending
Remaining: Brief 040 code/source binding, artifact regeneration, tests, review, and remote confirmation
Blockers: none for offline correction; T16.5b is closed
Training lock: closed
Next step: correct and mechanically bind the offline census to the pinned runtime
```

### 2026-07-11 - T16.5a remotely verified; T16.5b opened

```text
Current task: T16.5b
State: in_progress
Completed: T16.5a offline no-write census preflight remotely preserved with its same-agent review
Evidence: local HEAD, origin tracking, and git ls-remote all matched d002c8038ac1e393c5c92f4a2f215c961b408bf2; implementation f200087 and reviewer 047 are ancestors; unrelated dirty baseline remains 232 paths
Commit: f200087 implementation; d002c80 reviewer boundary
Remaining: offline live-adapter/discovery/camera/evidence tests, lease revalidation, then one bounded live read-only attempt
Blockers: none for offline implementation; live access fails closed on lease or identity ambiguity
Training lock: closed
Next step: execute Brief 039 offline gates before opening any device
```

### 2026-07-11 - T16.5a offline no-write census locally reviewed

```text
Current task: T16.5a
State: in_progress
Completed: code-pinned follower/six-servo fixture contract; narrow injected and recorded transports; complete ordered read lifecycle; bounded retry; dual-error cleanup; signed no-write trace/result; safe leader teardown
Evidence: implementation f200087; reviewer 047; 14 focused and 193 broad tests; contract 17e8c712...; trace 25cbac27...; result e7c0ecfc...; hardware_opened=false; physical_follower_commanded=false
Commit: f200087; review/remote preservation pending
Remaining: preserve implementation and reviewer evidence on origin, then close T16.5a and prepare the separately gated live read-only brief
Blockers: no offline blocker; live hardware remains closed until remote confirmation and lease revalidation
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.2b remotely verified; T16.5a opened offline

```text
Current task: T16.5a
State: in_progress
Completed: T16.2b mechanically computed qualification remotely preserved with its same-agent review
Evidence: local HEAD, origin tracking, and git ls-remote all matched 383557b0bdb1dc17725b4eac0db37d19c902b1c0; implementation 710960b and reviewer 046 are ancestors
Commit: 710960b implementation; 383557b reviewer boundary
Remaining: offline read-only transport/lifecycle preflight before any live discovery
Blockers: none for offline work; live hardware remains closed
Training lock: closed
Next step: execute Brief 038 using fake/recorded transports only
```

### 2026-07-11 - T16.2b mechanically computed qualification locally reviewed

```text
Current task: T16.2b
State: in_progress
Completed: code-pinned v2 metric rules; signed/content-addressed evidence and input; deterministic conservative aggregation; independent report recomputation; legacy caller-status closure; central-composer-only claims
Evidence: implementation 710960b; reviewer 046; 16 focused and 147 broad tests; spec eff5a15e...; input 5c942916...; report 7ed02c6e...; denial composition 41a4d731...; all global decisions withheld
Commit: 710960b; review/remote preservation pending
Remaining: preserve implementation and reviewer evidence on origin, then close T16.2b and start offline T16.5a
Blockers: no offline blocker
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.4b remotely verified; T16.2b opened

```text
Current task: T16.2b
State: in_progress
Completed: T16.4b deterministic numerical hardening remotely preserved with its same-agent review
Evidence: local HEAD, origin tracking, and git ls-remote all matched dbdd1ef019961cc6d7deba81f69a873c11efac5a; implementation 7d05629 and reviewer 045 are ancestors
Commit: 7d05629 implementation; dbdd1ef reviewer boundary
Remaining: mechanically generated and independently recomputed qualification results; offline T16.5a follows
Blockers: none for offline T16.2b
Training lock: closed
Next step: execute Brief 037
```

### 2026-07-11 - T16.4b numerical hardening locally reviewed

```text
Current task: T16.4b
State: in_progress
Completed: deterministic scale-normalized symmetric eigensolver; fixed iteration bound; eigenvector residual and orthogonality checks; scale-relative symmetry/PSD/triangle tolerances; finite-intermediate rejection; deterministic NumPy corpus
Evidence: implementation 7d05629; reviewer 045; 17 focused and 131 broad tests; 20,000 extreme-scale eigensystems and 2,000 randomized physical tensors; product identities unchanged; every global composer decision withheld
Commit: 7d05629; review/remote preservation pending
Remaining: preserve implementation and reviewer evidence on origin, then close T16.4b and start T16.2b
Blockers: no offline blocker
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.4b production compiler locally reviewed

```text
Current task: T16.4b
State: in_progress
Completed: rooted hierarchical exact-cover BOM; six production source modes; explicit units/calibration/metrology; content-addressed evidence; full-precision transforms/aggregation; fixture-only mixed-source artifact; current arm remains blocked
Evidence: implementation a93ff05; reviewer 044; 21 focused and 122 broad tests; fixture fe9dbd5468a606019db735dc8664c05d5fc207d94bdcbc84243f58cfa98f869f -> b8d7c5d287051aa863c3ef08597deefb9dd7685ad2c89d820456f92491fef25d; composer withholds all global decisions
Commit: a93ff05; remote preservation pending
Remaining: deterministic eigensolver convergence/residual and scale-relative numerical hardening before T16.4b closes
Blockers: remote preservation pending; no offline implementation blocker
Training lock: closed
Next step: preserve implementation/review on origin, then execute numerical-hardening brief
```

### 2026-07-11 - Owner-supervised physical proof steering

```text
Current task: T16.4b
State: in_progress
Completed: recorded ten-hour window extension and staged T16.5a/T16.5b/T16.5c/T16.6 authority; final operator confirmation granted for one exact initial micro-motion permit
Evidence: explicit owner steering while physically present beside the desk-mounted SO-101; persisted Goal remains active
Commit: pending scoped steering commit
Remaining: finish T16.4b and T16.2b before any T16.5a; no live hardware before verified T16.5a; no write/motion before exact session permit gates
Blockers: none for offline continuation
Training lock: closed
Next step: preserve steering on origin, then resume Brief 033
```

### 2026-07-11 - T16.2b-A central authority composition verified

```text
Current task: T16.4b
State: in_progress
Completed: versioned central authority contract and fail-closed composer; assembly-inertials v2 local-capability boundary; non-authorizing deterministic fixture decision
Evidence: implementation c0b9629; reviewer 043; 101-test broad gate; contract identity 6d04b20547a9391c4e695b5a337ee292410a2a13a8a3efdf34cb7033feda6ba1; denied composition d1206c5c710a280e4f7c5c448fd9ba59793b9850c2e9fd1bf962999ec82bc8ab; origin confirmed through e1d59ca
Commit: c0b9629 implementation; e1d59ca review evidence
Remaining: production hierarchical measured-inertial compiler, mechanically computed qualification, and offline census conformance
Blockers: none for offline T16.4b
Training lock: closed
Next step: resume Brief 033 without granting any global readiness from inertial output
```

### 2026-07-11 - Authority-composer-first redirect and overnight launch

```text
Current task: T16.2b-A
State: in_progress
Completed: accepted T16.4b strict artifact sub-slice as valid partial progress; recorded the central-composer architectural boundary; installed single-agent overnight instructions and launch prompt
Evidence: reviewer decision 042; Brief 034; AGENTS.md; .codex/config.toml; overnight-authority-twin-goal-loop.md
Commit: supplied by the scoped overnight-substrate commit containing this entry
Remaining: implement and verify T16.2b-A, resume production T16.4b, then T16.2b and offline T16.5
Blockers: none for offline continuation
Training lock: closed
Next step: implement Brief 034 in the separate top-level overnight Codex thread
```

### 2026-07-10 - T16.4b strict artifact and authority sub-slice

```text
Current task: T16.4b
State: in_progress
Completed: strict finite JSON/signing/reference layer; PSD and principal-moment inertia validation; unique measurement and exact prior graph checks; content-addressed synthetic evidence; explicit compilation/simulation/physical/promotion authority gates
Evidence: implementation commit 69df54d; reviewer decision 041; 35 focused tests; product CLI proves synthetic compilation succeeds while synthetic simulation-training authority fails
Commit: 69df54d
Remaining: production non-synthetic mixed-source measured intake, hierarchical BOM exact cover, explicit units/calibration, full-precision aggregation, golden fixture, and broad review
Blockers: none for offline continuation
Training lock: closed
Next step: continue brief 033 with the production mixed-source compiler path
```

### 2026-07-10 - T16.1b unified executable stack verified

```text
Current task: T16.4b
State: in_progress
Completed: T16.1b replaced split_runtime_unresolved with one exact LeRobot base plus tracked patch-set and routed collection, training, finalization, inference, and LeLab through a fail-closed stack identity
Evidence: implementation commit dca2b45; reviewer decision 040; stack identity c8e903e7f1b75215864719398c902d864d8cbd7f43e01f03ffb22c8de240a7a4; 13 stack/lock, 13 twin, 24 structural, and 24 measured-inertial tests passed
Commit: dca2b45
Remaining: T16.4b, T16.2b, revised T16.5
Blockers: none for offline T16.4b
Training lock: closed
Next step: execute brief 033
```

### 2026-07-10 - External review reopens production-authority boundaries

```text
Current task: T16.1b
State: in_progress
Completed: preserved exact df9ed0a branch and dirty-worktree evidence; accepted prior T16.1, T16.2, and T16.4 results only as inventory/schema/synthetic scaffold evidence
Evidence: reviewer decision 039; origin/codex/pi05-autolearn-loop points at df9ed0a4d2212819382a4701a33c263f2cdee32e; local status, binary patch, and integrity-checked untracked archive written outside the repo
Commit: pending
Remaining: unify executable stack, harden production measured-inertial authority, compute qualification mechanically, then restart revised T16.5
Blockers: none for offline T16.1b
Training lock: closed
Next step: execute brief 032
```

### 2026-07-10 - Reviewer closeout T16.4 and open T16.5

```text
Current task: T16.5
State: in_progress
Completed: reviewer reran brief 030 and confirmed the bounded synthetic_test_only measured-inertial compiler now preserves the ready happy path while failing closed for exact-cover ambiguity, reused evidence, and invalid rotation/inertia inputs; T16.4 is accepted as verified
Evidence: reviewer decision 038; independent reruns reproduced 24 focused measured-inertial tests, 69 broad robot-lab tests, blocked real identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4, and synthetic ready identity 9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d
Commit: pending
Remaining: first fake-bus/recorded-trace harness slice for a read-only servo census replay, then broader T16.5 fitting/qualification scaffolding
Blockers: none for offline continuation
Training lock: closed
Next step: execute brief 031 without opening hardware or claiming physical qualification
```

### 2026-07-10 - T16.4 synthetic ready negative matrix

```text
Current task: T16.4
State: in_progress
Completed: extended the bounded synthetic_test_only proof with explicit negative-matrix regressions for missing exact-cover atoms, duplicate active atom coverage, ambiguous multi-atom measurement selection, reused measurement evidence, invalid rotation matrices, and invalid inertia matrices; relaxed only the synthetic verifier precheck needed so incomplete-but-well-formed synthetic inputs fail through the exact-cover compiler path
Evidence: focused measured-inertial suite passed 24 tests including the six new negative cases; py_compile passed for measured_inertial_intake module/tests/CLI; live default --verify preserved blocked real identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; live default --verify --require-ready still exited nonzero with blocked_missing_measurements; live synthetic CLI write to /private/tmp/scenesmith-next-synthetic-ready.json still reached ready identity 9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d; broad robot-lab gate passed 69 tests
Commit: pending
Remaining: reviewer confirmation that brief 030 fully closes T16.4, then begin T16.5
Blockers: none for offline continuation
Training lock: closed
Next step: reviewer rerun of the negative matrix and bounded CLI paths, then open the smallest fake-bus/recorded-trace harness slice
```

### 2026-07-10 - T16.4 synthetic ready happy path

```text
Current task: T16.4
State: in_progress
Completed: added a bounded synthetic_test_only measured-inertial fixture and ready compiler branch; proved deterministic golden aggregate mass/COM/full inertia, stable semantic ready identity under reordered synthetic input, and hard-refused writes to either checked-in real current-arm destination
Evidence: tests/fixtures/robot_lab/measured_mass/synthetic_complete.json identity 412825dfedd4c5b015b81a2f4d32d208e6d1dbd6de547a665a8f92005acf8388; live synthetic CLI output identity 9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d with mass 4.5 kg, COM [0.35, 0.283333333, 0.033333333], inertia [[0.073625, -0.053025, 0.26218125], [-0.053025, 1.1719375, 0.0126125], [0.26218125, 0.0126125, 1.11475]]; default blocked identities remained 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; focused measured-inertial suite passed 18 tests; broad robot-lab gate passed 63 tests
Commit: pending
Remaining: expand the synthetic path from happy-path proof to the full negative matrix for exact-cover ambiguity, reused evidence, and invalid transform/inertia failures
Blockers: none for offline continuation
Training lock: closed
Next step: keep T16.4 open and land the negative matrix in the next slice without changing the default blocked real current-arm path
```

### 2026-07-10 - T16.4 custom absolute-path CLI safety correction

```text
Current task: T16.4
State: in_progress
Completed: preserved caller-provided absolute intake/output paths outside the repo for the measured-inertial CLI; added direct external-path write, verify, require-ready, and invalid-input no-overwrite regressions
Evidence: python -m unittest tests.unit.test_measured_inertial_intake (14 tests); python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py; python scripts/robot_lab/write_measured_inertial_intake.py --verify kept blocked identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; external temp-path live CLI write+verify succeeded with output identity e92738a2b9f450a72c693d67903eb75cbaa40a483a35c18f4a46cf09521e1478; external --require-ready rejected nonzero; forged external intake failed before overwrite and left output sha256 7fe752efca565caca826dbd1c12b052899b72235115cf7a3663eae9b1666b35e unchanged; broad gate ./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff passed 59 tests
Commit: pending
Remaining: synthetic_test_only ready fixture/compiler, exact-cover overlap and reused-evidence rejection, golden aggregate inertia proof, and stable ready identity checks
Blockers: none for offline continuation
Training lock: closed
Next step: keep T16.4 open and implement the bounded synthetic ready-state compiler path from brief 028
```

### 2026-07-10 - T16.4 custom CLI path defect added to closeout

```text
Current task: T16.4
State: in_progress
Completed: independent rerun confirmed all embedded-prior attacks fail and existing outputs remain unchanged
Evidence: valid canonical intake copied outside repo fails before CLI write/verify because _relative_to_repo unconditionally calls relative_to(REPO_ROOT) on absolute paths
Commit: pending
Remaining: support bounded absolute custom paths with correct artifact refs, then complete synthetic ready math and negative matrix
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 028; brief 027 is superseded
```

### 2026-07-10 - T16.4 embedded CAD prior integrity gap

```text
Current task: T16.4
State: in_progress
Completed: independent adversarial audit accepted the blocked proof state but tested re-signed nested evidence rather than only top-level refs
Evidence: re-signed changes to cad_priors[0] source path/hash/mass/transform were accepted; a 99 kg forged prior compiled and verified with cad_prior_summary 99.485006 kg; duplicate component records were also accepted
Commit: pending
Remaining: deterministic embedded-prior reconstruction/evidence validation and duplicate-ID rejection, then the synthetic ready compiler and full negative matrix
Blockers: none for offline correction; real measurements remain absent by design
Training lock: closed
Next step: execute brief 026; brief 025 is superseded
```

### 2026-07-10 - T16.4 embedded prior integrity correction

```text
Current task: T16.4
State: in_progress
Completed: awaiting-measurements verification now rejects re-signed nested CAD-prior tampering and duplicate component IDs by requiring deterministic equality with the repo rebuild before blocked assembly compilation can read the intake
Evidence: 10 focused measured-inertial tests including forged 99 kg CAD prior, duplicate component ID, and no-output-written regression; py_compile on module/tests/CLI; live CLI --write-intake and --verify preserved identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; 55-test broad robot-lab gate passed
Commit: pending
Remaining: synthetic_test_only ready compiler, exact-cover selection, overlap/reused-evidence rejection, inertia math golden fixture, and order-invariance checks
Blockers: none for offline implementation; real current-arm measurements remain absent by design
Training lock: closed
Next step: implement Part B of brief 026 without changing the default blocked real-artifact paths
```

### 2026-07-10 - T16.4 manager truth correction before implementation

```text
Current task: T16.4
State: in_progress
Completed: repo/history audit found no genuine physical SO-101 piece-weight evidence; seven MJCF masses totaling 0.632006 kg are CAD-derived priors only
Evidence: manager intervention 009; TwinProfile leaves full_arm_mass_kg null; no measured-mass source file exists
Commit: pending
Remaining: checked-in awaiting-measurements intake, blocked current-arm result, synthetic-only ready compiler proof, binding/tamper/double-count tests, and fresh review
Blockers: real current-arm inertials remain blocked until physical measurements are supplied, but the offline compiler capability is implementable now
Training lock: closed
Next step: execute brief 024; do not execute superseded brief 023
```

### 2026-07-10 - T16.4 blocked real-artifact baseline

```text
Current task: T16.4
State: in_progress
Completed: added deterministic measured-mass intake and assembly inertials artifacts for the checked-in current arm; normal CLI write emits `awaiting_measurements` intake plus `blocked_missing_measurements` output bound to the dependency lock, TwinProfile, structural diff, and intake file hash; `--verify` passes and `--require-ready` rejects nonzero
Evidence: configurations/robot_lab/pi05_measured_mass_intake.awaiting_measurements.json identity 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88; configurations/robot_lab/pi05_assembly_inertials.blocked_missing_measurements.json identity 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; 7 focused measured-inertial tests; live CLI write+verify; 52 broad robot-lab tests
Commit: pending
Remaining: synthetic_test_only ready-state compiler math, golden mass/COM/inertia fixture, overlap/double-count/tamper hard-fail coverage, and order-invariance checks
Blockers: real current-arm physical inertials remain blocked until future measurements exist; offline synthetic compiler proof is still implementable
Training lock: closed
Next step: extend `scenesmith.robot_lab.measured_inertial_intake` to compile a synthetic ready fixture without changing the default blocked real artifact
```

### 2026-07-10 - T16.3 manager reopen after adversarial identity checks

```text
Current task: T16.3
State: in_progress
Completed: independent manager audit reproduced the accepted v1 implementation and tested semantic invariants outside the executor suite
Evidence: scaled-equivalent quaternion spellings produced different unnamed keys; reversing same-stem duplicates with friction 1 versus 2 changed both collision and friction records; manager intervention 008
Commit: pending
Remaining: canonical quaternion identity hashing, deterministic full-attribute duplicate ordering, v2 strategy declaration, artifact regeneration, and fresh review
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 022; do not execute deferred brief 021
```

### 2026-07-10 - T16.3 unnamed-geom identity v2 correction

```text
Current task: T16.3
State: in_progress
Completed: unnamed collision-key hashing now canonicalizes equivalent explicit quaternions, same-stem duplicate occurrence suffixes are assigned after deterministic full-attribute sorting, signed-zero quaternion spellings collapse to the same canonical payload, and the tracked artifact now declares identity strategy v2
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9; 24 focused structural-diff tests; py_compile of structural diff, tests, and CLI; live CLI write+verify pass; 49 broad robot-lab tests
Commit: pending
Remaining: fresh reviewer rerun of the adversarial fixtures and live verify path to close T16.3
Blockers: none for offline correction
Training lock: closed
Next step: obtain a reviewer decision on brief 022 before reopening deferred brief 021 / T16.4
```

### 2026-07-10 - T16.3 reviewer closeout (superseded by manager intervention 008)

```text
Current task: T16.4
State: pending
Completed: reviewer verified order-invariant unnamed collision identities, duplicate multiplicity preservation, visual-sibling stability, and explicit non-pairing across incompatible runtime-vs-Menagerie structures
Evidence: reviewer decision 032; commit 07a652e; configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity 5b070b1b1f98aad3eaf00d4bd9d153ab78f53ec4046b0948ef2cf5ae93387683; 21 focused structural-diff tests; live CLI verify pass; 46 broad robot-lab tests
Commit: 07a652e
Remaining: measured inertial intake, offline qualification harness, then M17 compiler truth gate
Blockers: none for offline T16.4 implementation
Training lock: closed
Next step: compile measured-part mass inputs and fail closed on ambiguous assembly inertia/COM evidence
```

### 2026-07-10 - T16.3 semantic unnamed-geom identity

```text
Current task: T16.3
State: in_progress
Completed: structural diff now derives unnamed collision identities from a shared semantic key helper used by both collision and friction extraction, records the identifier strategy in the artifact, ignores visual-only sibling insertions, preserves duplicate multiplicity deterministically, and leaves incompatible runtime-vs-Menagerie structures as explicit missing/extra evidence instead of ordinal pairings
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity 5b070b1b1f98aad3eaf00d4bd9d153ab78f53ec4046b0948ef2cf5ae93387683; 21 focused structural-diff tests; live CLI write+verify pass; 46 broad robot-lab tests
Commit: pending
Remaining: reviewer confirmation for T16.3 closeout
Blockers: none for offline correction
Training lock: closed
Next step: obtain a reviewer decision on brief 020 and, if accepted, reopen T16.4 measured-mass intake
```

### 2026-07-10 - T16.3 unnamed-geom proof strengthened

```text
Current task: T16.3
State: in_progress
Completed: source/profile binding, effective solver defaults, quaternion semantics, inferred-inertia unknowns, and effective contact/friction evidence
Evidence: commit d31cdc3; manager audit 007 proves repeat-generation alone cannot detect sibling-index instability
Commit: pending
Remaining: order-invariant semantic unnamed-geom identity
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 020 and obtain a fresh reviewer decision
```

### 2026-07-10 - T16.3 inertial and contact truthfulness correction

```text
Current task: T16.3
State: in_progress
Completed: structural diff now surfaces non-derivable mass-bearing inertials as explicit unknown evidence and compares friction/contact through real attached joints and collision geoms while keeping declaration-only defaults separate
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity fe9177e07a597e9db57c1896f5295f84b7ae9ff313219e33afa83b41c46fd08d; 15 focused structural-diff tests; live CLI write+verify pass; 40 broad robot-lab tests
Commit: pending
Remaining: deterministic unnamed-geom limits
Blockers: none for offline correction
Training lock: closed
Next step: finish the deterministic unnamed-geom handling needed to reopen T16.4
```

### 2026-07-10 - T16.3 complete quaternion semantic coverage

```text
Current task: T16.3
State: in_progress
Completed: structural diff now applies quaternion canonicalization across all transform-bearing structural categories, treats omitted transform quaternions as effective identity where MuJoCo defaults apply, and tolerates tiny canonical quaternion noise
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity a90ffc8b347ae8b6d4a7a4bde0d60c3be64af7a41fb77b543e2c6c9beb6b9331; 12 focused structural-diff tests; live CLI write+verify pass; 37 broad robot-lab tests
Commit: pending
Remaining: inferred-inertia unknown handling, effective friction/contact attachment semantics, and deterministic unnamed-geom limits
Blockers: none for offline correction
Training lock: closed
Next step: resume brief 016 and make inertial/contact truthfulness explicit without reopening quaternion false deltas
```

### 2026-07-10 - T16.3 quaternion coverage correction

```text
Current task: T16.3
State: in_progress
Completed: TwinProfile binding and effective solver comparison; partial rotation canonicalization
Evidence: commit fb54e64; five scale-equivalent arm-collision quaternion deltas remain in the artifact; manager audit 006
Commit: pending
Remaining: collision/implicit-identity quaternion semantics, inferred-inertia unknowns, effective friction/contact evidence, and deterministic identifier limits
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 017, then return to queued brief 016
```

### 2026-07-10 - T16.3 semantic acceptance reopened

```text
Current task: T16.3
State: in_progress
Completed: deterministic source/hash plumbing and first machine diff baseline
Evidence: commit 7bebf55; manager audit 005; independent semantic audit
Commit: pending
Remaining: profile binding, canonical rotations, effective solver semantics, inferred-inertia unknowns, effective friction/contact evidence, and regression tests
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 014 and obtain a fresh reviewer decision before T16.4
```

### 2026-07-10 - T16.3 TwinProfile binding correction

```text
Current task: T16.3
State: in_progress
Completed: structural diff now binds the checked-in simulation-only TwinProfile as an explicit artifact input and rejects profile drift during verify
Evidence: commit 936dd2f; local write/verify product path; 6 focused tests; 31 broad robot-lab tests
Commit: 936dd2f
Remaining: canonical rotations, effective solver defaults, inferred-inertia unknowns, effective friction/contact evidence, and deterministic identifier limits
Blockers: none for offline correction
Training lock: closed
Next step: normalize equivalent quaternions and compare effective solver defaults before reopening T16.3 for review
```

### 2026-07-10 - T16.3 quaternion and solver semantics correction

```text
Current task: T16.3
State: in_progress
Completed: structural diff now canonicalizes equivalent quaternions for semantic comparison, records compared canonical quaternion values on true rotation mismatches, and compares effective MuJoCo solver defaults even when one source omits <option>
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity 6a990b8a28d6b18e12dde18398122ea84ba7d3a91569ca2f728d8c09f5d3dad7; 9 focused structural-diff tests; live write+verify product path; 34 broad robot-lab tests
Commit: pending
Remaining: inferred-inertia unknown handling, effective friction/contact attachment semantics, and deterministic unnamed-geom limits
Blockers: none for offline correction
Training lock: closed
Next step: close the remaining T16.3 semantic gaps before reopening T16.4
```

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

### 2026-07-10 - T16.1 manager redirect

```text
Current task: T16.1
State: in_progress
Completed: local LeLab, dirty LeRobot patch, Robot Studio MJCF/URDF identities
Evidence: commit 92adde5; reviewer commit ec788fc; manager audit found OpenPI/Menagerie revision=null and absolute repo_root
Commit: correction pending
Remaining: portable remote pins before T16.2
Blockers: none
Training lock: closed
Next step: correct the dependency lock and re-review T16.1
```

### 2026-07-10 - T16.1 completed and planning realigned

```text
Current task: T16.2
State: in_progress
Completed: portable local/remote dependency lock including actual Menagerie so101.xml
Evidence: commits 92adde5, addcafd, cd5ab42; 81 tests; live offline lock verify
Commit: cd5ab42 final content correction
Remaining: twin schemas, structural reconciliation, mass compiler, fake qualification harness
Blockers: none for T16.2
Training lock: closed
Next step: content-addressed simulation-only twin contract
```

### 2026-07-10 - T16.2 truth correction and T16.3 start

```text
Current task: T16.3
State: in_progress
Completed: twin profile/spec/report schemas without fabricated measurement evidence
Evidence: bc5187c schema feature; ae6fe04 removes invented pass/12 V value; 94 tests
Commit: ae6fe04
Remaining: structural diff, measured-mass compiler, offline qualification harness
Blockers: none for structural diff
Training lock: closed
Next step: compare pinned runtime and Menagerie structures without switching either
```

### 2026-07-10 - T16.3 false blocker cleared

```text
Current task: T16.3
State: in_progress
Completed: tracked exact Menagerie license, README, so101.xml, and scene.xml
Evidence: commit 38b3425; vendored hashes match remote pin; 95 tests
Commit: 38b3425
Remaining: machine structural diff and reconciliation decision
Blockers: none for offline work
Training lock: closed
Next step: resume structural comparison from tracked source inputs
```

### 2026-07-10 - T16.3 structural baseline verified

```text
Current task: T16.4
State: in_progress
Completed: deterministic structural diff between the active Robot Studio MJCF and pinned Menagerie so101.xml, with matched/mismatched/missing/extra buckets and explicit reconciliation decisions
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity d71576574eb3dbb592cb495481a9de2e17e1581cc3e10476e1bc098106053b89; 5 focused structural-diff tests; live CLI write+verify pass; 17-test broad robot-lab suite pass
Commit: pending
Remaining: measured inertial intake, offline qualification harness, then M17 compiler truth gate
Blockers: none for offline T16.4 implementation
Training lock: closed
Next step: compile measured-part mass inputs and fail closed on ambiguous assembly inertia/COM evidence
```

### 2026-07-10 - T16.1 robotics dependency lock

```text
Current task: T16.2
State: verified
Completed: pinned LeLab runtime, split local LeRobot checkout, OpenPI semantic reference, Robot Studio SO-101 runtime files, and Menagerie target lineage in one tracked lock
Evidence: configurations/robot_lab/pi05_robotics_dependency_lock.json; 7 tests passing in .mujoco_venv; live lock write+verify pass; active MJCF/URDF hashes recorded; local lerobot tracked diff sha256 captured
Commit: pending
Remaining: twin profile, qualification schemas, structural reconciliation, and downstream compiler gates
Blockers: none for offline work; unrelated broad-suite provenance test still needs an importable lerobot package in the validation environment
Training lock: closed
Next step: define TwinProfile, TwinQualificationSpec, and TwinQualificationReport with a simulation-only example tied to the new dependency lock
```

### 2026-07-10 - T16.1 portable remote pin correction

```text
Current task: T16.2
State: verified
Completed: replaced unresolved OpenPI and Menagerie placeholders with exact remote revisions plus license/content hashes; removed absolute repo_root from the signed lock identity
Evidence: updated configurations/robot_lab/pi05_robotics_dependency_lock.json; 7 focused dependency-lock tests passing; live write+verify pass; 11-test broad robot-lab suite pass including scene-builder reachability
Commit: pending
Remaining: twin schemas, structural reconciliation, and downstream compiler gates
Blockers: none for offline work
Training lock: closed
Next step: define TwinProfile, TwinQualificationSpec, and TwinQualificationReport with a simulation-only example tied to the corrected dependency lock
```

### 2026-07-10 - T16.2 twin contract schemas

```text
Current task: T16.3
State: verified
Completed: content-addressed TwinProfile, TwinQualificationSpec, and TwinQualificationReport schemas plus checked-in simulation-only example artifacts bound to the corrected dependency lock
Evidence: configurations/robot_lab/pi05_twin_profile.simulation_only.json; configurations/robot_lab/pi05_twin_qualification_spec.simulation_only.json; configurations/robot_lab/pi05_twin_qualification_report.simulation_only.json; 10 focused twin-contract tests; live write+verify pass; 21-test broad robot-lab suite pass
Commit: pending
Remaining: Menagerie vs Robot Studio structural diff, measured inertial intake, and offline qualification harness
Blockers: none for offline work
Training lock: closed
Next step: reconcile the active Robot Studio SO-101 runtime against pinned Menagerie with a machine-readable structural diff and explicit no-switch semantics
```

### 2026-07-10 - T16.3 blocked on missing Menagerie sources

```text
Current task: T16.3
State: blocked
Completed: confirmed the active runtime MJCF is present locally and that the dependency lock only records Menagerie `robotstudio_so101` as an exact remote pin plus reference-file hashes
Evidence: configurations/robot_lab/pi05_robotics_dependency_lock.json pins `robotstudio_so101/so101.xml` and `robotstudio_so101/scene.xml`; repo search finds no local `robotstudio_so101` directory or Menagerie XML sources to diff against
Commit: pending
Remaining: vendor or otherwise track the pinned Menagerie structural XML sources, then generate the machine-readable diff artifact
Blockers: brief 011 requires a CLI that resolves both runtime and Menagerie sources from repo state, which is impossible while only remote hashes are tracked locally
Training lock: closed
Next step: add the pinned Menagerie `robotstudio_so101` source files to repo state under a tracked path and resume T16.3 without switching the active runtime inputs
```
### 2026-07-10 - T16.3 reviewer closeout after v2 identity correction

```text
Current task: T16.4
State: pending
Completed: independent reviewer reruns confirmed equivalent quaternion spellings now hash to the same unnamed identities, same-stem duplicates are occurrence-assigned independent of sibling order, py_compile stayed clean, live artifact verify stayed bound to the checked-in baseline, and the broad robot-lab gate remained green
Evidence: reviewer decision 033; commit cadc0f3; configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9; 24 focused structural-diff tests; live CLI verify pass; 49 broad robot-lab tests
Commit: cadc0f3
Remaining: measured-part mass intake, offline qualification harness, then M17 compiler truth gate
Blockers: none for offline T16.4 implementation
Training lock: closed
Next step: compile measured-part mass inputs and fail closed on ambiguous assembly inertia/COM evidence through brief 023
```
