# Experience Compiler And Hardware Twin Task Ledger

Updated: 2026-07-13

```text
training_lock: closed
run_window: start 2026-07-13T12:30:11-05:00; no new major slice after 19:45:11; hard closeout 20:30:11 CDT
run_state: T16.5c verified as a negative sorting-checkpoint transfer diagnosis; live gate closed; training lock closed
current_milestone: M17/M19 grasp execution track
current_task: T19.0l pending; construct a geometry-derived unilateral-jaw grasp and full unassisted lift trajectory
completed: T16.0 guard; T16.1 dependency inventory; T16.1b unified executable stack; T16.2/T16.2b mechanically computed qualification; T16.2b-A central authority composition; T16.3 structural baseline; T16.4/T16.4b production measured-inertial compiler and numerical hardening; corrected T16.5a offline no-write census preflight
evidence: bracket 040305a7...; antipodal v2 strict 950e7568...; contact-face audit 23572851... proves fixed pad on +z in 30/30 bilateral aggregates and moving pad on -y in 27/30; no new hardware or motion
remaining: T19.0 truthful gripper/contact semantics; strict unassisted MuJoCo grasp; T19.2 bounded physical calibration under fresh permits; M17 Experience Compiler grasp episodes; simulation-training authority
owner_authority: completed disconnect scope was exactly one follower call with inherent torque-disable plus response/status/zero-holder proof; permit is consumed and cannot be reused; reconnect only if proven no-motion-safe; initial supervised_micro_motion confirmation remains separately gated
blockers: sorting scene mismatch; no metric camera/workcell transform; large policy proposal; two jaw bodies contact one local object region without force closure; no physical aperture/current mapping
next_step: compute the fixed/moving pad midpoint at each requested close target, offset pregrasp so that midpoint rather than fixed-adjacent gripperframe targets the object, and rerun identical candidates
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
| T16.5b | verified | T16.5a | Live read-only census and finite physical camera capture while owner-present lease is active | Attempt 006; private `125de28f...`; original manifest v4 `eff3c824...`, mechanically migrated manifest v5 `5218c3bd...`; exact two-camera 640x480 capture; 54 no-write reads; six torque-off values; sequential evidence only |
| T16.5c | verified | T16.5b | Real-observation preprocessing, PI0.5 shadow, and matched MuJoCo replay with no actuation | Negative transfer diagnosis verified through Brief 094/Reviewer 120: physical bracket/camera roles and diagnostic preprocessing/proposal/corrected consequence replay observed; sorting deployment input, matched physical replay, motion, transfer, qualification, and training withheld |
| T16.6 | pending | T16.5a-T16.5c | Exact initial supervised physical POC under final owner confirmation | Signed/content-addressed session permit; no-op-equivalent then at most one small one-joint delta and exact return; no second prompt; active lease; requested/projected/sent/measured separate; `supervised_micro_motion` only |

### 2026-07-13 - Brief 093 antipodal contact gate

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: v2 analytic antipodal gate verified; actual grasp still rejected; live gate closed; training lock closed
V1 preservation: strict fixture remains byte-identical at 4f0bad3c...
V2 requirements: distinct jaws; span >= 0.02 m; normal dot <= -0.8; contact-axis alignment >= 0.8
Positive: declared analytic expert semantic success; not policy, MuJoCo, physical, or full-wrench proof
Negatives: all 17 fail, including exact 4.907838 mm collapsed span, same jaw, same side, misalignment, malformed, and non-finite witnesses
Artifact: 950e7568... identity; 5ac9c96e... file SHA-256; 246755 bytes
Authority gained: strict_grasp_antipodal_contact_proxy_fixture_conformant only
Authority withheld: actual grasp, full 6D wrench closure, strict policy, physical twin, simulation training, optimizer, and motion
Next step: orientation/lateral MuJoCo search compiled through v2 and full unassisted phases
```

### 2026-07-13 - Brief 092 contact span and friction/compliance sweep

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: contact geometry/sweep observed; force closure and friction-only grasp rejected; live gate closed; training lock closed
Contact profile: 19 simultaneous-jaw frames; span collapses 32.86691 mm to 4.907838 mm during hold
Interpretation: two named jaw bodies contact one local region; contact count alone is not opposing force closure
Training grid: 12 friction x contact-time settings; zero lift successes; no selected candidate
Holdout: friction 4.0 / 0.01 s excluded from selection; also fails; final object z 0.322867 m
Artifact: 89c04062... identity; 8860549b... file SHA-256; 10245 bytes
Authority gained: mujoco_contact_span_profile_observed and bounded_contact_property_sweep_observed only
Authority withheld: force closure, strict/policy grasp, physical aperture/twin, simulation training, optimizer, and motion
Next step: orientation/lateral search with opposing normals, span, wrench closure, impact, and full unassisted phases
```

### 2026-07-13 - Brief 091 low-impact two-jaw search

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: low-impact two-jaw contact accepted; unassisted lift rejected; live gate closed; training lock closed
Search: 20 fixed wrist-roll x pregrasp-height candidates; same nominal object/model/seed/close target
Selected: wrist roll -1.5 rad; height 0.018 m; 11 two-jaw close frames; 8/8 prelift hold frames; peak 4.1971684 N
Lift: no weld/assist; only 4 two-jaw lift frames; 0/12 lift-hold frames; final object z 0.324974 m below required 0.35 m
Joint evidence: two-jaw contact at 0.2395 to 16.724525 gripper percent; metric aperture not inferred
Artifact: 5a5de249... identity; fa250ee6... file SHA-256; 186089 bytes
Authority gained: low_impact_two_jaw_mujoco_contact_candidate_observed only
Authority withheld: unassisted/strict/policy grasp, metric aperture, physical qualification, simulation training, optimizer, and motion
Next step: geometry-derived aperture plus bounded friction/compliance/close-hold sweep with held-out setting
```

### 2026-07-13 - Brief 090 first MuJoCo anchor grasp attempt

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: deterministic attempt observed and strict grasp rejected; live gate closed; training lock closed
Object: nominal nonphysical 50 x 35 x 30 mm, 25 g turquoise anchor cousin
Rollout: two exact 371-frame replays; complete non-image state/action/contact/assist/object/gripper trace retained
Legacy score: placement pass after contact-gated weld assistance; not unassisted or policy grasp success
Strict result: fail on 17.081659463 N peak impact, missing current and aperture calibration, one-sided grasp contact, invalid stable hold, and contact-retaining release
Artifact: 32f14feb... identity; 831fdf2a... file SHA-256; 439297 bytes
Verification: 9 focused tests; 69-test relevant broad gate; Brief 089 fixture byte-identical
Authority gained: deterministic_mujoco_anchor_grasp_attempt_observed only
Authority withheld: unassisted/strict/policy grasp success, physical profile, twin qualification, simulation training, optimizer, and motion
Next step: low-impact two-jaw pregrasp/close, nominal simulation aperture profile, stable hold, and clean release
```

### 2026-07-13 - Brief 089 strict anchor grasp evaluator

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: evaluator fixture verified; T16.5c still in progress; live gate closed; training lock closed
Physical anchor: visible small lightweight turquoise rectangular candidate bound to accepted external frame; dimensions, mass, COM, material, friction, and pose unknown
Nominal cousin: declared analytic simulation geometry and mass; no physical-measurement claim
Positive: one ordered analytic-expert trace passes semantic strict-grasp success and remains pure_policy_success=false
Negatives: all 12 adversarial traces fail through the same evaluator for their expected reasons
Artifact: 4f0bad3c... identity; 3be8ac16... file SHA-256; 133859 bytes
Verification: deterministic fixture exact; 6 focused tests in each repository runtime; 66-test relevant broad gate
Authority gained: strict_grasp_evaluator_fixture_conformant only
Authority withheld: MuJoCo grasp validity, physical anchor profile, policy success, physical twin qualification, simulation training, optimizer work, and motion
Next step: execute a deterministic anchor-cousin grasp in pinned MuJoCo and feed measured trace through the unchanged evaluator
```

### 2026-07-13 - Brief 088 midpoint coordinate replay correction

```text
Current task: T16.5c
State: in_progress; live gate closed; training lock closed
Cause: legacy simulation-policy shoulder/elbow offsets were applied to the pinned midpoint-calibrated physical-pose model
Correction: preserve legacy v1; add a separately versioned fail-closed midpoint-direct candidate for offline physical-pose diagnostics
Candidate review: b98445cb...; direct identity selected for offline replay only; metric transform and twin qualification false
Replay: a0179263...; horizons 5/10/15 twice exactly; zero start/action projection; zero robot self-contact; zero warnings; near-zero cube motion
Remaining rejection: physical scene mismatch, no metric camera/workcell transform, invalid policy input, wrist-roll support mismatch, 54.4099-degree first wrist change, 5.43238 rad/s maximum simulated velocity
Verification: 188 focused tests in each pinned runtime; 293-test broad authority/twin gate; legacy dependency/preprocessing/reviewed-input/fixture and twin/authority identities remain byte-stable
Authority gained: midpoint pose candidate and corrected prefix-replay diagnostic observations only
Authority withheld: accepted input/shadow, matched replay, safe_enough_to_prepare_t16_6, motion, qualification, training, Brev, and paid compute
Next step: first executable offline Minimum Viable Grasping Twin slice around the visible turquoise anchor
```

### 2026-07-13 - Brief 087 current physical preprocessing, shadow, and replay diagnostic

```text
Current task: T16.5c
State: in_progress; live gate closed; training lock closed
Inputs: accepted private-success v2 final frames, reviewed external/wrist roles, exact q_after, exact sorting prompt
Preprocessing: 57acad57...; exact tensors 89644c19... / 8041d823... / missing 811b0abf...; wrist roll outside observed checkpoint min/max
Inference: exact local revision 84b551af... and weights 471adf9a...; real MPS two-pass fixed-noise equality; finite 50x6 chunk 4d350587...
Proposal finding: first wrist-roll delta 54.4099 degrees; maximum chunk deltas include 55.8645 wrist roll and 51.5712 elbow flex; DO_NOT_ACTUATE
Replay: 42499e46...; horizons 5/10/15 twice exactly; no warnings; near-zero cube motion; shoulder lift/elbow start projection and every-action projection; shoulder/lower-arm self-contact
Authority gained: diagnostic tensor, proposal, and prefix-control-replay observations only
Authority withheld: accepted live input, accepted policy shadow, matched replay, safe_enough_to_prepare_t16_6, motion, qualification, training, Brev, and paid compute
Next step: offline measured-pose coordinate and collision reproduction; do not open a motion gate
```

### 2026-07-13 - Brief 084 private current-frame retention

```text
Current task: T16.5c
State: in_progress; accepted session remains v1; live gate closed; training lock closed
Experiment-derived gap: accepted bracket retained four frame hashes and semantics but not current pixel bytes, blocking real preprocessing
Correction: future successful sessions emit private-success v2 with four exact source-bound PNGs; result/receipt/tracked review remain hash-only; v1 remains verifiable
Verification: targeted red then green; 183 focused tests per pinned runtime; 382 broad tests in 121.863 seconds; source verifiers in both runtimes; actual accepted v1 verifies in both; compile/workflow/JSON/privacy/diff checks
Authority gained: private_source_bound_current_frame_retention_conformant only
Authority withheld: accepted live policy input, preprocessing, model, inference, shadow, replay, motion, qualification, training, and paid compute
Next step: remote confirmation, then a separately reviewed finite bracket with fresh profile, discovery, lease, holder preflight, and no-torque cleanup
```

### 2026-07-13 - Brief 074 unselected AVFoundation source correction

```text
Current task: T16.5c
State: in_progress; live gate open; sessions started zero; training lock closed
Failure: fresh macOS discovery added AVFoundation-only Capture screen 0; candidate construction rejected before contract or device open
Correction: require system-camera names to be a subset of AVFoundation names; resolve static-pose selections only from sources with exact system identities; selecting the screen source still rejects
Actual evidence: discovery 4c29fe9c... resolves RealSense index 0 and C922 index 1; candidate preflight f8555cad...; hardware_accessed false
Verification: 78 focused tests per pinned runtime; 378 broad tests; both source verifiers in both runtimes; diff checks
Authority gained: unselected_avfoundation_source_tolerance_conformant only
Authority withheld: live observation acceptance, reviewed input, model, inference, replay, motion, qualification, and training
Next step: remote confirmation, fresh profile and lease, then the one allowed candidate session
```

### 2026-07-13 - Live candidate rejected; gate consumed and closed

```text
Current task: T16.5c
State: in_progress; gate closed; sessions started one; training lock closed
Attempt: t16-5c-20260713-0845-cdt
Failure: camera-frame normalization rejected invalid fields after session start; no success result or receipt issued
Evidence: discovery 673ff2d2...; profile 69e86eda...; lease 43fc0c72...; contract e6bf4f62...; immutable failure b117e797...
Shutdown: Studio follower disconnected; torque false; leader connected; canonical/TTY holders [0,0]
Authority: no observation, reviewed input, policy, replay, motion, qualification, or training label
Next step: one narrow offline frame-contract correction; any future live attempt requires a new reviewed gate
```

### 2026-07-13 - Brief 076 live frame metadata adapter verified offline

```text
Current task: T16.5c
State: in_progress; prior gate closed/consumed; training lock closed
Reproduced mismatch: pinned generic reader returns 5 semantic fields plus exact receive-start/finish timestamps; strict runtime accepts exactly 5 semantic fields
Correction: pinned live adapter validates exact field set and increasing nonnegative integer receive interval, rejects unknown/missing/invalid metadata, then returns unchanged semantic view
Verification: targeted test red then green; 79 focused tests per pinned runtime; 379 broad in 124.646 seconds; both source verifiers in both runtimes; compile/diff checks
Authority gained: live_static_pose_frame_metadata_adapter_conformant only
Authority withheld: live gate/session, observation acceptance, reviewed input, model, inference, replay, motion, qualification, and training
Next step: remote preservation, then a separately reviewed fresh gate and full preflight
```

### 2026-07-13 - Brief 071 Full Access/no-prompt runtime policy verified offline

```text
Current task: T16.5c
State: in_progress; Brief 071 verified and remotely preserved; live gate closed
Completed: trusted project default plus explicit hardware profile now require danger-full-access/never; formal doctor, same-thread runtime evidence, candidate gate, and redacted review require the same no-prompt semantics; profile-purpose instructions remain distinct
Evidence: implementation 19b7e766f31e4bf5702e454c62606165bf023dc5; reviewer 097; profile hashes 65edfaff.../0fce3e51.../66378a47...
Verification: 96 proof-ladder tests in each pinned runtime; 70 static-pose tests in each; 371-test authority/twin gate; both source verifiers in both runtimes; compile/JSON/workflow/state-alignment/diff checks
Adversarial: restricted or interactive defaults; on-request profile/turn/doctor; stale/cross-thread/changed runtime; profile field/content drift; permissions cannot grant gate, lease, session, proof label, training, or motion authority
Authority gained: full_access_no_prompt_runtime_profile_contract_conformant only
Authority withheld: live candidate session, accepted static pose, reviewed production input, policy shadow, replay, actuation, T16.5c verification, T16.6 permit, qualification, training
Runtime at Brief 071 review: live-ineligible because that earlier task was managed/restricted; a fresh task had to prove danger-full-access/never
Hardware: none; no discovery/open, serial/camera/Studio, model, MuJoCo, motion, optimizer, training, Brev, or paid compute
Training lock: closed
Next step: canonical review reconciliation, then a fresh no-prompt Full Access task and separate remotely confirmed one-session gate
```

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
| T19.0 | verified | T16.3,T16.5c | Establish truthful simulated gripper geometry and contact semantics before grasp search | Brief 095/Reviewer 121; audit `9bfce4c6...`; 3 bodies/12 geoms; original composite collisions non-pad; explicit pad boxes; 5.238-130.944 mm simulation reference aperture; order-independent inward-normal proof; 174-test broad gate |
| T19.0b | verified | T19.0 | Make grasp orientation and object yaw independently controllable and verified before search | Brief 096/Reviewer 122; fixture `cdcb2359...`; 4/4 candidates; exact wrist/yaw; max residual 0.538 mm; requested/achieved axes; collision-free; 176-test broad gate |
| T19.0c | verified | T19.0,T19.0b | Run deterministic bounded geometry-first grasp search without friction/compliance tuning | Brief 097/Reviewer 123; 12 Halton candidates + untouched holdout; 10 reachable; zero pad contacts/eligible; composite jaw occlusion isolated; 178-test broad gate |
| T19.0d | verified | T19.0c | Correct explicit-pad collision occlusion without tuning friction or search ranges | Brief 098/Reviewer 124; identical rerun; 3 candidates/277 positive fixed-pad contacts up to 4.338 N; zero moving-pad/bilateral contacts; 180-test broad gate |
| T19.0e | verified | T19.0d | Center object on predicted pad midpoint instead of gripperframe/fixed-pad reference | Brief 099/Reviewer 125; identical 12 candidates + excluded holdout; 2 bilateral candidates through 8/8 hold frames; zero strict-v2/eligible; 182-test broad gate |
| T19.0f | verified | T19.0e | Separate object-yaw/table settling from gripper-induced preclose motion | Brief 100/Reviewer 126; 6/12 approach-motion-valid; 2 bilateral through 8/8 hold frames; zero strict-v2/eligible; 184-test broad gate |
| T19.0g | verified | T19.0f | Align the gripper closing axis with an anchor principal axis before search | Brief 101/Reviewer 127; 4 candidates at 0.806-0.886 alignment; 2 motion-valid; zero bilateral/strict-v2/eligible; 186-test broad gate |
| T19.0h | verified | T19.0g | Jointly solve wrist flex and roll for a horizontal principal-axis closing vector | Brief 102/Reviewer 128; zero solutions at >=0.95 x-axis alignment and <=0.1 vertical; zero contact/eligible; 188-test broad gate |
| T19.0i | verified | T19.0h | Evaluate both anchor x and y principal axes under the same horizontal gate | Brief 103/Reviewer 129; 8 y-axis aligned, 6 motion-valid, 2 bilateral through 8/8 hold, zero strict-v2/eligible; 190-test broad gate |
| T19.0j | verified | T19.0i | Center the target along the selected closing axis while retaining transverse offset | Brief 104/Reviewer 130; 8 centered, 6 motion-valid, 2 bilateral through 8/8 hold; max span 20.965 mm; alignment <=0.052; zero strict-v2/eligible; 192-test broad gate |
| T19.0k | verified | T19.0j | Audit actual contact faces and normals for centered bilateral candidates | Brief 105/Reviewer 131; candidates 2/3 source-identical; fixed pad +z 30/30; moving pad -y 27/30; convention proof valid/order-independent; 194-test broad gate |
| T19.0l | pending | T19.0k | Build geometry-derived unilateral-jaw close/hold/lift/lower/release proof | Derive close q from 35 mm selected width and aperture curve; pad midpoint at object-center height; bounded fixed-jaw clearance; two-pass deterministic unchanged-evaluator trajectory |
| T19.1 | pending | M16, read authority | Run read-only servo/firmware/register census | Immutable hardware snapshot; no writes or motion |
| T19.2 | pending | T19.1, motion authority | Calibrate cameras, joint offsets, kinematics, timing, and gripper aperture | Held-out reprojection, pose, and timing tolerances |
| T19.3 | pending | T19.1-T19.2, motion authority | Identify delay, saturation, settling, directionality, backlash, friction, compliance | Per-joint fitted distributions and held-out trajectory evidence |
| T19.4 | pending | T19.2-T19.3, contact authority | Identify fingertip/table friction, slip, force/current, and object profiles | Held-out grasp/lift/slip/release envelope |
| T19.5 | pending | T16.4, T19.2-T19.4 | Fit posterior and run held-out qualification | Every TwinQualificationSpec metric passes or is explicitly failed |
| T19.6 | pending | T19.5, M17 | Bind qualified twin hash and requalification triggers to all downstream artifacts | Contract/hardware drift blocks execution |

## M20 / Gate C - Cheap Falsification And Clean Supervision

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T20.1 | pending | M17-M18 | Freeze one clean simulation-only single-cube dataset, split, structural twin, prompts, seeds, and semantic-success proof contract | Immutable train/evaluation specification with explicit `simulation_only` authority; terminal outcome and strict task success are distinct signed fields |
| T20.2 | pending | T20.1 | Overfit one to three episodes with ACT | Near-zero train error plus closed-loop behavior change |
| T20.3 | pending | T20.1 | Repeat tiny overfit with PI0.5 | Same falsification evidence and physical semantics |
| T20.4 | pending | T20.2-T20.3 | Add explicit accumulation and run 250/500/1,000 optimizer-update MPS ladder | Updates distinct from microbatches; finite gradients; exact sample audit |
| T20.5 | pending | T20.4 | Sweep PI0.5 execution horizons 5/10/15 with chunk size 50 | Same weights/seeds; queue resets and open-loop duration recorded |
| T20.6 | pending | T20.2-T20.5 | Run fixed one-cube phase-level and adversarial outcome-versus-strict evaluation | Ordered approach/contact/grasp/lift/transport/release/placement/retreat witness; putt, slide, throw, scripted-motion, assistance-relabel, stage-drift, and actor-privilege cases preserve truthful outcomes but fail strict success |
| T20.7 | pending | T20.1, T20.6 | Bake off PI0.5, SmolVLA, ACT, and Diffusion Policy | Same semantics, splits, samples seen, seeds, and proof modes |
| T20.8 | pending | T20.6-T20.7 | Accept or reject simulation policy using semantic strict success; separately evaluate transfer eligibility | `simulation_policy_accepted` requires repeatable strict success rather than terminal occupancy; `physical_transfer_eligible` remains false until M19 passes |

The external-example disposition and adversarial semantic-success requirements are
recorded in `docs/autonomous-workflow/so-frame-adoption-decision.md`. They add no
current dependency, runtime, checkpoint, model asset, training authority, or
hardware authority.

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

### 2026-07-12 - Brief 062 desktop-resume hardware-profile correction verified

```text
Current task: T16.5c
State: in_progress; exact current turn hardware-profile eligible; live gate closed; training lock closed
Completed: resumed session metadata may repeat only when all existing fields remain exact and only memory_mode is added; latest exact turn still controls the runtime decision
Evidence: implementation d404778; turn 7d245960...; profile 4ade6d50...; on-request; danger-full-access; hardware_accessed false
Verification: 177 focused tests in each pinned runtime; live doctor/profile capture; py_compile; diff checks; 376 broad tests in 102.558 seconds
Adversarial: changed thread, cwd, git, timestamp, source, CLI, provider, field removal, unexpected addition, existing-value mutation, stale never turn, profile drift, or before/after runtime drift still reject before hardware
Authority gained: current same-thread hardware-supervised runtime eligibility only
Authority withheld: live gate, device discovery/open, observation acceptance, reviewed input, tensors, model, inference, shadow, replay, actuation, qualification, and training
Next step: separately review, commit, push, and remote-confirm one fresh finite static-pose gate before discovery
```

### 2026-07-12 - Brief 061 preflight rejected; live gate closed unused

```text
Current task: T16.5c
State: in_progress; live gate closed; session count zero
Failure: formal hardware-profile capture rejected before discovery because one rollout contained repeated session metadata and concurrent active turn IDs with contradictory on-request and never policies
Safety: no USB, serial, camera, servo bus, holder discovery, model, policy, replay, training, or paid compute access; no private session outcome artifact required because the session never started
Correction: do not weaken the active-runtime verifier or select a favorable stale context; end the conflicting turn and start one unambiguous hardware-supervised on-request parent
Authority gained: none
Authority withheld: all live observation, reviewed input, tensor, model, shadow, replay, actuation, qualification, and training labels
Next step: push this fail-closed transition, repair the app thread permission mode between turns, then open a new separately reviewed finite gate
```

### 2026-07-12 - Brief 060 one-session T16.5c live gate transition

```text
Current task: T16.5c
State: in_progress; live gate open only after this transition commit is confirmed on origin
Window: 2026-07-12T10:55:00-05:00 through 2026-07-12T11:25:00-05:00; one session; fresh five-minute owner-presence lease required
Runtime: active thread 019f5372... independently observed danger-full-access, on-request, permission profile disabled
Allowed: metadata discovery; canonical and TTY zero-holder checks; exact identity/calibration/640x480-at-30 verification; six Present_Position reads before; two frames per signed camera; six Present_Position reads after; no-torque close; post-close all-alias zero-holder check; one immutable private outcome artifact
Forbidden: handshake, configuration or register writes, torque changes, motion commands, policy execution, training, retries of the overall session, reconnect, paid compute
Authority gained: one fresh static-pose candidate session only after remote confirmation
Authority withheld: static_pose_bracketed_observation, reviewed physical policy input, model load, inference, policy shadow, replay, actuation, qualification, training
Next step: commit, push, confirm remote, then perform fresh profile/lease/discovery/holder preflight and the one decisive bracket
```

### 2026-07-11 - Brief 059 PI0.5 training-support semantics correction verified offline

```text
Current task: T16.5c
State: in_progress; Brief 059 verified and remotely preserved; live gate closed
Completed: versioned v2 fixture artifact; exact nine-vector training-statistic binding; mean/std, bin, quantile, and observed-min-max recomputation; pure isolated support module; explicit no-clamp/no-mode-switch contract
Evidence: implementation f6b6c08; artifact b20e0782...; runtime 1642f75c...; normalizer 8dc4c304...
Verification: 175 focused tests in .mujoco_venv; 175 in pinned LeLab runtime; exact writers/gates; compilation/privacy/diff checks; 374 broad tests in 86.332 seconds
Correction: [-1,1] is a textual discretizer reference, not a hard input domain; wrist_flex alone is outside observed training min-max and q01-q99; gripper is within q01-q99 and min-max support
Parity: fixture input, prompt, bins, state, preprocessor tensors, tokens, model images/masks, model-call contract, action/queue contract, and frame evidence are byte-identical to Brief 058
Authority gained: fixture_pi05_training_support_audit_conformant only beyond the existing fixture tensor-parity capability
Authority withheld: real reviewed input, static_pose_bracketed_observation, policy_shadow_input_valid, model/weight load, inference, shadow, replay, hardware, actuation, qualification/transfer, promotion, training
Hardware: none; current parent remains live-ineligible
Training lock: closed
Next step: fresh hardware-supervised on-request parent, finite run window, separate reviewed live gate, fresh lease/discovery/all-alias zero-holder proof; apply v2 support audit before policy shadow
```

### 2026-07-11 - Brief 058 fixture PI0.5 model-ready tensor parity verified offline

```text
Current task: T16.5c
State: in_progress; Brief 058 verified and remotely preserved; live gate closed
Completed: four deterministic complete PNGs; signed top/wrist role and highest-frame selection; calibrated q_after; exact CPU checkpoint processor and tokenizer; exact 224x224 model images/masks; token, prompt, tensor, action-horizon, and queue-reset hashes/contracts
Evidence: implementation 77724e1; artifact configurations/robot_lab/pi05_fixture_model_ready_tensor_parity.json; identity 559b9dbd...; runtime identity 4c89ca10...
Verification: 153 focused tests in .mujoco_venv; 153 in pinned LeLab runtime; exact tensor writer; Brief 056/057 writers; static fixture; compile/privacy/path/diff checks; 352 broad tests in 82.674 seconds
Finding (superseded by Brief 059): wrist_flex and gripper exceed mean±std, but only wrist_flex is outside observed training support; [-1,1] is not a hard validity domain for this serialized MEAN_STD checkpoint
Adversarial: source/gate/static-result substitution; fixture-live relabeling; camera/frame/PNG/state/task/token/tensor/mask/action/horizon/queue drift; false model/weight/network/hardware/inference/replay claims; runtime/path/privacy violations
Authority gained: fixture_pi05_model_ready_tensor_parity_conformant only
Authority withheld: real reviewed-input bundle, accepted live policy input, static_pose_bracketed_observation, policy_shadow_input_valid, model/weight load, inference, policy shadow, MuJoCo replay, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio, reconnect, write, torque, or motion; current parent remains live-ineligible
Training lock: closed
Next step: fresh hardware-supervised on-request parent, finite run window, separate reviewed live gate, fresh lease/discovery/all-alias zero-holder proof; no hardware in this parent
```

### 2026-07-11 - Brief 057 PI0.5 reviewed-input issuance gate verified offline

```text
Current task: T16.5c
State: in_progress; Brief 057 verified and remotely preserved; live gate closed
Completed: strict signed schemas and composition gate for future live-session acceptance, stable-camera-to-top/wrist role binding, and exact reviewed task prompt; exact source/session/issuer/review-record/validity/evidence-class consistency; fixture/production separation
Evidence: implementation 44dd871; artifact configurations/robot_lab/pi05_reviewed_inputs.blocked_missing_reviewed_inputs.json; schema scenesmith.pi05_reviewed_input_gate.v1; identity 0f6362f6...; all three input slots absent
Verification: 123 focused tests in .mujoco_venv; 123 in pinned LeLab runtime; Brief 056 and Brief 057 writers/verifiers in both runtimes; py_compile; whitespace/privacy/source/diff checks; 322 broad tests in 69.292 seconds
Adversarial: self-signed authority and extra-field escalation; source/issuer/scope/subject/session/review-decision drift; future/expired/boolean/oversized validity; manifest substitution; fixture/production mixing; partial bundles; camera identity/role/model ambiguity; numeric-index/raw-identity leakage; missing private-review hash; task whitespace/underscore/multiline/control/Unicode-normalization/hash drift; review-record path/hash/marker and input path alias substitution
Real inputs created: none; no live-session acceptance artifact, stable-camera role assignment, or reviewed task prompt exists
Authority gained: pi05_reviewed_input_issuance_gate_conformant only
Authority withheld: pi05_reviewed_input_bundle_valid, accepted_live_policy_input, static_pose_bracketed_observation, policy_shadow_input_valid, model/tokenizer/processor construction, model-weight load, preprocessing, inference, policy shadow, MuJoCo replay, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, model weight, optimizer, or paid compute
Training lock: closed
Next step: separately reviewed offline fixture preprocessing conformance or later real reviewed inputs; production preprocessing and live gate remain closed
```

### 2026-07-11 - Brief 056 PI0.5 preprocessing source contract verified offline

```text
Current task: T16.5c
State: in_progress; Brief 056 verified and remotely preserved; live gate closed
Completed: deterministic signed source contract for the exact PI0.5 executable files, cached checkpoint processor and tokenizer revisions, six-wide normalizer statistics, physical coordinate semantics, prompt template, and sole CUDA-to-CPU preprocessing override
Evidence: implementation fd49820; artifact configurations/robot_lab/pi05_policy_input_preprocessing.blocked_missing_inputs.json; schema scenesmith.pi05_preprocessing_source_contract.v1; identity f6b21668...; checkpoint revision 84b551af...; tokenizer revision 35e4f464...
Verification: 114 focused tests in .mujoco_venv; 114 in pinned LeLab runtime; all execution/candidate/camera/calibration/static-fixture/dependency/source-contract verifiers in both runtimes; py_compile; whitespace/privacy/source/diff checks; 313 broad tests in 70.328 seconds
Adversarial: executable source and runtime drift; cache revision/escape/file and ancestor alias substitution; checkpoint config/order/device drift; safetensors malformed header/offset/overlap/gap/boolean/non-finite/wrong-width/nonpositive/fractional statistics; tokenizer/coordinate drift; fixture/live relabeling; blocker, camera-role, task, acceptance, and authority fabrication
Blocked inputs: accepted_live_session_review_decision; reviewed_stable_camera_role_binding; reviewed_task_prompt
Authority gained: pi05_policy_input_preprocessing_source_contract_conformant only
Authority withheld: accepted_live_policy_input, static_pose_bracketed_observation, policy_shadow_input_valid, model/tokenizer/processor construction, model-weight load, preprocessing, inference, policy shadow, MuJoCo replay, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, model weight, optimizer, or paid compute
Training lock: closed
Next step: separate fixture-only reviewed-input issuance gate; production preprocessing and live gate remain closed
```

### 2026-07-11 - Brief 055 redacted live-session review manifest verified offline

```text
Current task: T16.5c
State: in_progress; Brief 055 verified and remotely preserved; live gate closed
Completed: complete historical private-success/receipt/source re-verification before deterministic redaction; exact candidate-pending-review schema; private-path-free source, drift, timing, frame, holder, and lifecycle summaries; exclusive session-named tracked writer with reread
Evidence: implementation 411e5cc; schema scenesmith.static_pose_live_session_review_manifest.v1; no actual live manifest instance written or accepted
Verification: 107 focused tests in .mujoco_venv; 107 in pinned LeLab runtime; all execution/candidate/camera/calibration/static-fixture source verifiers; py_compile; duplicate-dict/privacy/source/diff checks; current parent live-profile negative proof; 306 broad tests in 69.782 seconds
Adversarial: failure artifact and fixture/live relabeling; contract/profile/result/static-source/private-evidence/receipt/reference/root substitution; source and manifest authority escalation; raw path/report/identity/position leakage; field drift; output escape/wrong name/parent alias/overwrite/corruption; boolean operation count and frame index
Authority gained: redacted_static_pose_live_candidate_session_review_conformant only
Authority withheld: actual live review manifest, live candidate acceptance, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Current runtime: live-ineligible because persisted active turn_context approval_policy is never
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: fixture-only PI0.5 policy-input preprocessing source contract; live gate remains closed
```

### 2026-07-11 - Brief 054 fail-closed live-session orchestrator verified offline

```text
Current task: T16.5c
State: in_progress; Brief 054 verified and remotely preserved; live gate closed
Completed: one production entry point that reverifies the active profile, complete candidate contract, new private destination, and exact one-shot factories before session start; exactly-one immutable private outcome; candidate result withholding; signed candidate-only receipt
Evidence: implementation ce7a794; receipt schema scenesmith.static_pose_live_session_receipt.v1; private-reference digest plus contract/profile/result/evidence/root linkage; ancestor-symlink hardening
Verification: 101 focused tests in .mujoco_venv; 101 in pinned LeLab runtime; all execution/candidate/camera/calibration/static-fixture source verifiers; py_compile; duplicate-dict/diff checks; current parent live-profile negative proof; 300 broad tests in 92.360 seconds
Adversarial: profile/contract/destination/factory preflight rejection; private destination reuse and ancestor alias; candidate and cleanup error groups; failed or regressed outcome clocks; success/failure build, verify, write, and reference failures; receipt build/verification failure; contract/profile/result/evidence/reference/authority/time substitution; no retry or second write
Authority gained: fail_closed_static_pose_live_session_orchestrator_conformant only
Authority withheld: live candidate result, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Current runtime: live-ineligible because persisted active turn_context approval_policy is never
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline redacted candidate-session review manifest; live gate remains closed
```

### 2026-07-11 - Brief 053 live-execution interlocks verified offline

```text
Current task: T16.5c
State: in_progress; Brief 053 verified and remotely preserved; live gate closed
Completed: safe owner-interactive project default plus separate hardware/offline profiles; active-turn-context and explicit doctor cross-check; full-contract/profile-gated one-shot Feetech and exact-name FFmpeg factories; candidate result v2 hardware-profile linkage; fixed exclusive content-addressed private success/failure evidence
Evidence: implementation d76baf5; project/hardware/offline profile hashes 977e1b42.../dfce70f4.../76c188c5...; FFmpeg 8.0.1 / 0a96da27...; hardware profile schema v1; candidate result v2; private success/failure v1
Verification: 90 focused tests in .mujoco_venv; 90 in pinned LeLab runtime; matching source/profile/Feetech/FFmpeg verifiers; py_compile; duplicate-dict/source/diff checks; current parent live-profile negative proof; 289 broad tests in 73.993 seconds
Adversarial: child config cannot mask parent never policy; cross-thread/stale/synthetic/re-signed/changed-during-capture runtime evidence rejects; profile symlink/config drift rejects; unpinned Feetech/path/protocol/alias drift rejects; camera identity/mode/frame/binary drift rejects; factory reuse rejects; result/profile substitution and success/failure relabeling reject; private session reuse, symlink, path escape, and content drift reject
Authority gained: pinned_static_pose_live_factory_spec_conformant, private_static_pose_live_candidate_evidence_conformant, and hardware_supervised_runtime_profile_validator_conformant only
Authority withheld: live candidate result, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Current runtime: live-ineligible because persisted active turn_context approval_policy is never; checked-in profile changes do not alter the running parent
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline fail-closed production-session orchestrator and exactly-one private artifact path; live gate remains closed
```

### 2026-07-11 - Brief 052 source-bound static-pose candidate verified offline

```text
Current task: T16.5c
State: in_progress; Brief 052 verified and remotely preserved; live gate closed
Completed: fixed production/fixture contract and result classes; exact project-state gate snapshot, lease, follower USB/all-alias, stable-camera fresh-index, calibration/static-source, operation-count, timing, and no-write lifecycle binding; candidate-only production result
Evidence: implementation 79eee89; verification follow-up 2c0b903; contract/result schemas scenesmith.static_pose_live_candidate_contract.v1/scenesmith.static_pose_live_candidate_result.v1; accepted discovery b57fbec8...; follower USB c5bd66ff...; stable cameras 69d55167... and 9931d030...
Verification: 77 focused tests in .mujoco_venv; 77 in pinned LeLab runtime; accepted private-discovery source resolver in both runtimes; manifest/profile/static/source verifiers; py_compile; safety/privacy/diff/JSON checks; 276 broad tests in 72.567 seconds
Adversarial: fixture/live evidence-class re-signing; stale or consumed gate; scope/session/window/review drift; expired lease; project-state digest drift; follower USB/alias/path substitution; stable-camera ambiguity/index churn/mode drift; holder/lifecycle/count/timing/pose drift; write/torque/motion/unexpected-operation audit; constructor/primary/release/close/post-holder failure preservation
Authority gained: static_pose_live_candidate_contract_valid and source_bound_static_pose_live_candidate_runtime_conformant only
Authority withheld: live candidate result, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Live prerequisites missing: fresh finite run window; actual hardware_supervised_on_request/on-request runtime; separate reviewed remote gate transition; fresh owner-presence lease; fresh discovery and all-alias zero-holder snapshots
Next step: separate offline exact Feetech/FFmpeg factory, immutable private evidence, and execution-profile validator slice; live gate remains closed
```

### 2026-07-11 - Brief 051 stable camera identity binding verified offline

```text
Current task: T16.5c
State: in_progress; Brief 051 verified and remotely preserved; live gate closed
Completed: manifest v5 migration from exact accepted v4/private evidence; full capture-selection digest retained; stable name/unique-ID/model-ID/input-mode digest excludes only numeric index; calibration/static-pose/runtime source chain regenerated under v2 bracket schemas
Evidence: implementation bff160d; private 125de28f... unchanged; manifest 5218c3bd.../file 4311ffc2...; stable cameras 69d55167... and 9931d030...; profile 24db6f24...; contract/observation/result 7260be3e.../9ad35d18.../6b40e275...
Verification: 67 focused tests in .mujoco_venv; 67 in pinned LeLab runtime; four offline artifact/source verifiers; py_compile; privacy/diff/JSON checks; 266 broad tests in 79.568 seconds
Adversarial: numeric index churn preserves only stable digest; name/unique-ID/model-ID/mode churn changes it; malformed/duplicate/re-signed digests reject; v4 compatibility grants no stable capability and cannot satisfy pinned v5 consumers; private file refs rehashed; path traversal and arbitrary migration sources rejected
Authority gained: stable_camera_identity_binding_valid only; prior calibration and fixture capabilities preserved on regenerated identities
Authority withheld: live bracket/permit, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline source-bound live-candidate contract/runner, then another review before any live-gate transition
```

### 2026-07-11 - Brief 050 injected static-pose runtime verified offline

```text
Current task: T16.5c
State: in_progress; Brief 050 verified and remotely preserved; live gate closed
Completed: source-verified contract entry; signed pre/post all-alias holder checks; exact construct/connect/q_before/two-camera/q_after/no-torque-close sequence; strict global monotonic clock; fixture transport and camera audits; nested observation/evaluation; exception grouping and cleanup
Evidence: implementation 4f75a7a; runtime schema scenesmith.static_pose_bracket_runtime_result.v1; fixture_static_pose_bracket_runtime_conformant only
Verification: 27 focused contract/runtime tests in .mujoco_venv; 27 in pinned LeLab runtime; py_compile; privacy/diff checks; 265 broad tests in 84.573 seconds
Adversarial: live-adapter refusal before connect; construction/connect/before/after read failure; camera open/read/release and paired failures; close plus holder failure; nonzero holders; audit writes/torque/motion/unexpected operations; camera semantics/property writes/continuous capture; bus drop; clock regression; pose drift; resigned authority/holder/lifecycle/nested evidence
Authority gained: fixture_static_pose_bracket_runtime_conformant only
Authority withheld: live candidate/permit, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Hardware: none; no discovery/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline source-bound live-candidate contract and runner, then another review before any live-gate transition
```

### 2026-07-11 - Brief 049 static-pose bracket contract verified offline

```text
Current task: T16.5c
State: in_progress; Brief 049 verified and remotely preserved; live gate closed
Completed: exact six-joint q_before/camera/q_after contract; profile-based degree/percent conversion; 0.5-degree/0.5-percent drift limits; strict monotonic enclosure; five-second bracket cap; exact no-write lifecycle counts; two accepted camera identities/modes; all-alias holder and no-torque teardown requirements
Evidence: contract 90e7baea43ebc059c09ef45b615c5808cf74abbbab87948a23536666acb43ceb; fixture observation 84d0aa12...; fixture result 6ebb9bd6...; implementation 4fd1f3a remote
Verification: 11 focused tests in .mujoco_venv; 11 focused tests in pinned LeLab runtime; independent fixture/profile rebuild; py_compile; privacy/diff checks; 249 broad tests in 75.655 seconds
Adversarial: source/tolerance/authority substitution; extra observation/nested fields; missing/duplicate/wrong identities; boolean/noninteger/out-of-range positions; body/gripper drift; time order/duration; camera identity/mode/dimension/hash; writes/torque/motion/count drift
Authority gained: static_pose_bracket_contract_valid and fixture_static_pose_bracket_conformant only
Authority withheld: real static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, physical qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, simulation replay, optimizer, or paid compute
Training lock: closed
Next step: separate offline fake-transport integration into the bounded live orchestrator, followed by independent review before any live-gate reconsideration
```

### 2026-07-11 - Overnight authority/twin run closeout

```text
State: scheduled closeout after the 11:44:07 no-new-major-slice cutoff; T16.5c remains in progress
Verified tasks: T16.2b-A central composer; T16.4b production compiler on fixture evidence; T16.2b computed qualification on fixture evidence; T16.5a offline no-write conformance; T16.5b live read-only census/capture
Latest partial: Brief 048 signed calibration profile b360b4f6... verified and remote at 700be05; canonical closeout remote through 7100c1c
Accepted physical labels: live_read_only_census_observed; physical_observation_capture
Authority withheld: synchronized/policy-valid observation, policy_shadow, motion, physical qualification/transfer, promotion, training
Safety: live gate closed; training lock closed; follower remained virtually disconnected with torque reported off; no motion command was sent
Remaining: static-pose bracket and coordinate validation; PI0.5 preprocessing/shadow; matched MuJoCo replay; only then separately gated T16.6 permit work
Next: open one offline static-pose-bracket/coordinate-contract brief in a new session; do not inherit a live session or motion permit
```

### 2026-07-11 - Brief 048 signed calibration profile verified offline

```text
Current task: T16.5c
State: in_progress; Brief 048 verified and remotely preserved; live gate closed
Completed: strict parsing of exactly six named joints/IDs; signed STS3215 homing-offset and raw-range bounds; drive mode zero; live model/firmware binding; body degree normalization; gripper 0=closed and 100=open semantics
Evidence: profile b360b4f60077846c62128fe4d4cc33d1ee4e6e72aa7831fcb7c6706e6b6599b4; calibration 192404b6.../770 bytes; manifest eff3c824.../file cd4120f0...; servo digest 66e9d363...; commit 700be05 remote
Verification: 6 focused adversarial tests; offline artifact rebuild; py_compile; git diff check; 238-test authority/twin regression in 87.588 seconds
Adversarial: missing/extra/duplicate/wrong joint identity; booleans/nonintegers; inverted/out-of-domain ranges; invalid homing offset/drive mode; calibration or manifest substitution; resigned normalization/polarity/global-authority drift
Authority gained: local calibration_profile_semantically_valid only
Authority withheld: static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, physical qualification, transfer, promotion, training
Hardware: none; no serial/camera/Studio access, reconnect, write, torque change, motion, policy inference, optimizer, or paid compute
Training lock: closed
Next step: close out the run, then design the static-pose-bracket and coordinate-validation slice before any preprocessing or shadow inference
```

### 2026-07-11 - T16.5b attempt 006 accepted

```text
State: verified; live gate closed at 2026-07-11T11:24:24-05:00
Discovery/contract: b57fbec8... / cf1ad99c...; fresh lease 3d9494b6...; RealSense uyvy422 640x480@30 and C922 yuyv422 640x480@30
Servo: 54 reads, zero retries/writes/torque changes/motion; all six Torque_Enable=0; no-torque close
Camera: four PNGs, all decoded 640x480 and exact-mode matched; two finite subprocesses; release/wait success; no stderr, terminate, kill, or residual process
Ownership: both signed serial aliases [0,0] before and after; snapshot b33a7cc0...
Evidence: tracked manifest eff3c824.../file cd4120f0...; private 125de28f.../file 02a264bd...; all bundle refs independently rehashed
Labels: live_read_only_census_observed; physical_observation_capture
Limits: sequential host receive intervals only; not synchronized, not policy-shadow-input-valid, not physical qualification, not motion authority
Next: T16.5c offline parsed calibration, static-pose bracket design/capture gate, PI0.5 preprocessing/shadow, matched MuJoCo replay; no actuation
```

### 2026-07-11 - Brief 047 signed 640x480 mode floor verified offline

```text
Current task: T16.5b
State: in_progress; Brief 047 verified offline; live gate closed for separate review
Selection: signed modes must be at least 640x480 and support integer 30 fps within 0.01; then choose smallest area and reviewed pixel-format priority; no default or cross-camera fallback
Actual discovery regression: C922 yuyv422 640x480@30; RealSense uyvy422 640x480@30; sub-floor 160x90 and 424x240 excluded
Evidence: e68068a remote; 53 focused tests; 33 LeLab-runtime camera tests; 232 broad tests in 71.477 seconds; actual discovery selection; offline/compile/diff checks
Hardware: none during Brief 047; live gate closed; no discovery/open, Studio request, reconnect, write, torque change, motion, policy, optimizer, or paid compute
Training lock: closed
Next step: canonical closeout, then separate final-session gate decision only if safe window remains
```

### 2026-07-11 - Brief 046 exact output dimensions verified offline

```text
Current task: T16.5b
State: in_progress; Brief 046 verified offline; live gate closed; Brief 047 active offline
Completed: named FFmpeg capture rejects parsed PNG dimensions that differ from signed mode before frame return; captured-frame/private-success and manifest layers independently recheck exact dimensions
Actual evidence: corrected manifest builder rejects attempt-005 private candidate ebb4934c... for 424x240-to-640x480 camera-1 drift
Verification: 6eb5f89 remote; 53 focused tests; 33 LeLab-runtime camera tests; 232 broad tests in 71.943 seconds; both offline verifiers; actual candidate rejection; pycompile; authority/privacy/diff checks
Hardware: none during Brief 046; live gate closed; no discovery/open, Studio request, reconnect, signal, write, torque change, motion, policy, optimizer, or paid compute
Remaining practical gap: deterministic smallest-area selection chose a signed 424x240 RealSense mode that live capture did not honor; both cameras have signed 640x480@30.000030 alternatives
Training lock: closed
Next step: Brief 047 signed 640x480-minimum selection offline
```

### 2026-07-11 - T16.5b live attempt 005 rejected; output-dimension drift

```text
Current task: T16.5b
State: in_progress; live gate closed; Brief 046 active offline
Discovery: v2 session t16-5b-20260711-1105-cdt; identity b8b11e74...; 209 C922 modes and 26 RealSense modes; zero devices opened during metadata discovery
Contract: v3 f76ea66f...; lease 4680d13a...; camera 0 yuyv422 160x90@30; camera 1 yuyv422 424x240@30
Servo/holder safety: 54 reads, zero retries/writes/torque changes/motion; all six Torque_Enable=0; no-torque close; both signed aliases [0,0] before and after; no ffmpeg process
Candidate capture: four valid PNGs; camera 0 observed 160x90 and matched; camera 1 observed 640x480 and contradicted signed 424x240 mode
Verifier gap: current v4 private/manifest verifier accepted the mismatched dimensions; post-run same-agent audit rejected the session
Evidence: private candidate ebb4934c.../file c341fdf3... retained ignored; candidate manifest 0d7b4400.../file 095ea665... removed; accepted proof labels []
Forbidden effects: no reconnect, Studio POST, signal, write, torque change, motion, policy, optimizer, paid compute, or physical qualification
Training lock: closed
Next step: canonical rejection closeout, then Brief 046 exact output-dimension enforcement offline
```

### 2026-07-11 - One fresh discovery-v2/contract-v3 session gated

```text
Current task: T16.5b
State: in_progress; one-session gate effective only after scoped transition commit is confirmed on origin
Window: 2026-07-11T11:04:00-05:00 through 2026-07-11T11:34:00-05:00; session limit one; fresh five-minute owner-presence lease required
Scope: fresh discovery v2 with metadata-only per-camera supported modes; zero holders across both signed aliases; contract v3 exact per-camera input modes; 54-read six-servo census with all Torque_Enable=0; no-write close; zero holders; two finite exact-name PNG frames per pinned camera; stable rediscovery and v4 evidence finalization
Failure: any mismatch rejects, writes no success manifest or proof label, cleans up, and immediately recloses the gate; no retry implied
Forbidden: reconnect, Studio POST, signal, register/configuration write, torque transition, motion, policy actuation, qualification, optimizer, or paid compute
Evidence: implementation 820a40f; canonical closeout a6da4b4; reviewer 067; disconnect proof 627de4fd...; all-alias holder snapshot b33a7cc0...
Training lock: closed
Next step: remotely confirm transition, then execute exactly once and reclose
```

### 2026-07-11 - Brief 045 signed per-camera input modes verified offline

```text
Current task: T16.5b
State: in_progress; Brief 045 verified offline; live gate closed for separate review
Discovery: v2 binds exact name/unique ID/model ID plus normalized finite pixel format, dimensions, and frame-rate ranges from AVCaptureDevice format metadata without AVCaptureSession or frame streaming
Selection: smallest frame area, then reviewed pixel-format priority; integer 30 fps must fall within signed range using only 0.01-fps AVFoundation matcher tolerance
Contract/command: v3 selects each camera from its own signed modes; exactly one -pixel_format, -video_size, and -framerate precedes each AVFoundation input
Evidence: diagnostic v3, private success v4, private failure v4, and tracked manifest v4 bind exact input mode; attempt-003 v2 and attempt-004 v3 private failures still verify
Adversarial: empty/unknown/duplicate/non-finite modes, identity mismatch, legacy discovery reuse, cross-camera substitution, malformed mode, coordinated resigned contract/diagnostic/result substitution, command reordering/duplication, stderr/nonzero/PNG/cleanup failures
Verification: 820a40f remote; 52 focused tests; 32 LeLab-runtime camera tests; 231 broad tests in 74.938 seconds; both offline verifiers; Swift typecheck; legacy artifact verification; pycompile; authority-surface/privacy/diff checks
Hardware: none during Brief 045; no discovery/open, Studio request, reconnect, signal, write, torque change, motion, policy, optimizer, or paid compute
Training lock: closed
Next step: canonical closeout, then separate one-fresh-session live-gate review
```

### 2026-07-11 - T16.5b live attempt 004 rejected; pixel-format cause retained

```text
Current task: T16.5b
State: in_progress; live gate closed; Brief 045 active offline
Discovery: session t16-5b-20260711-1036-cdt; identity 2e63871a...; four serial candidates and two exact-name cameras; zero devices opened during discovery
Contract: v2 b9b3c7ec...; five-minute lease f993a7c7...; integer 30 fps; two frames per pinned camera
Servo result: f5c6d17e...; 54 reads, zero retries/writes/torque changes/motion; six model 777 servos; all six Torque_Enable=0; one successful no-torque close
Serial ownership: both signed paths [0,0] before open, after close, and after failure; snapshot b33a7cc0...
Camera failure: first exact-name camera; return 0; strict subprocess_stderr rejection; 339 stderr bytes hash 80b01de5...; 5,244,174 stdout bytes hash 11bcb1c0...; yuv420p unsupported; supported list uyvy422/yuyv422/nv12/0rgb/bgr0
Private evidence: v3 identity 785241af...; file 305c42fb...; 40,640 bytes; complete contract/result independently verified; diagnostic bd722dd7...
Cleanup: release succeeded; no ffmpeg process; no success bundle, tracked manifest, proof label, reconnect, Studio POST, signal, write, torque change, motion, policy, optimizer, or paid compute
Training lock: closed
Next step: canonical rejection closeout, then Brief 045 offline per-camera supported-mode contract
```

### 2026-07-11 - One fresh v2-contract live session gated

```text
Current task: T16.5b
State: in_progress; one-session gate effective only after scoped transition commit is confirmed on origin
Window: 2026-07-11T10:33:00-05:00 through 2026-07-11T11:13:00-05:00; session limit one; fresh five-minute owner-presence lease required
Scope: fresh discovery; zero holders across both signed aliases; v2 exact 30-fps contract; 54-read six-servo census with all Torque_Enable=0; no-write close; zero holders; two finite exact-name PNG frames per pinned camera; stable rediscovery and evidence finalization
Failure: any mismatch rejects, writes no success manifest or proof label, cleans up, and immediately recloses the gate; no retry implied
Forbidden: reconnect, Studio POST, signal, register/configuration write, torque transition, motion, policy actuation, qualification, optimizer, or paid compute
Evidence: implementation 4ae0521c; canonical closeout cee8240; reviewer 064; disconnect proof 627de4fd...; all-alias holder snapshot b33a7cc0...
Training lock: closed
Next step: remotely confirm transition, then execute exactly once and reclose
```

### 2026-07-11 - Brief 044 explicit camera mode verified offline

```text
Current task: T16.5b
State: in_progress; Brief 044 verified offline; live gate closed for separate review
Completed: v2 live contract binds 30 fps; ffmpeg command places one -framerate 30 before -i; v2 diagnostic and v3 private/tracked evidence bind mode; v3 failure embeds full contract and servo result; legacy v1/v2 verification retained
Basis: attempt-003 diagnostic advertises 30.000030; installed ffmpeg 8.0.1 default is ntsc; AVFoundation source matches rates within 0.01 fps, so integer 30 differs by 0.000030
Evidence: 4ae0521c remote; 50 focused tests; 30 LeLab-runtime camera tests; 229 broad tests in 76.974 seconds; both offline verifiers; deterministic proof/fixture verification; legacy attempt-003 artifact verification; py_compile; diff check
Adversarial: missing/noninteger/non-30 contract mode; wrong/misordered command mode; audit drift; coordinated contract/result substitution; nonzero torque; missing full result; legacy compatibility
Hardware: none during Brief 044; no discovery/open, Studio request, reconnect, signal, write, torque change, motion, policy, training, or paid compute
Training lock: closed
Next step: canonical closeout, then separate one-fresh-session live-gate review
```

### 2026-07-11 - T16.5b live attempt 003 rejected; framerate cause retained

```text
Current task: T16.5b
State: in_progress offline; live gate closed; Brief 044 active
Session: t16-5b-20260711-1005-cdt; discovery 7a187d11...; contract 63979ed4...; lease 527ad754...
Census: 54 read successes; zero retries/writes/torque changes/motion; no-torque close success; pre/post/final holder counts [0,0]
Failure: first named-camera ffmpeg returned 251; diagnostic 482064ad...; stderr 13,548 bytes/64a8d5ff...; 29.970030 fps unsupported and 30.000030 advertised
Evidence: private rejection e7f8eb21.../6148b56e... retained; release success; zero ffmpeg processes; no success manifest; proof labels empty; physical_follower_commanded=false
Limitation: failure schema v2 binds servo result identity 2128192c... and counts but not full decoded servo/trace evidence
Safety: follower not reconnected; no Studio request, signal, write, torque transition, motion, policy, training, or paid compute
Training lock: closed
Next step: commit/push rejection; implement Brief 044 explicit 30 fps contract and full failure-servo evidence offline
```

### 2026-07-11 - Brief 043 live gate opened for one fresh session

```text
Current task: T16.5b
State: in_progress; live gate open after remote confirmation only; one-session limit; valid through 10:43 CDT
Prerequisites: 7ea26651 implementation and 37108426 canonical closeout remote; proof 627de4fd...; permit consumed; holder b33a7cc0... counts [0,0]; Torque_Enable trace gate verified offline
Allowed sequence: fresh metadata discovery; zero holders across canonical plus paired TTY; five-minute owner-presence lease; exact content-addressed no-write contract; six-servo census; no-write close; zero holders; finite named-camera batches; stable discovery; private bundle and tracked redacted manifest
Mandatory: all six Torque_Enable values zero; handshake false; disconnect disable_torque false; zero writes/motion; physical_follower_commanded=false; reclose gate on success or failure
Withheld: reconnect, motion, policy actuation, synchronized/policy-input-valid claim, physical qualification, training
Hardware: none during this state transition
Training lock: closed
Next step: commit/push/confirm transition, then execute exactly one fresh session
```

### 2026-07-11 - Brief 043 state-integrity gates verified offline

```text
Current task: T16.5b
State: in_progress; Brief 043 verified offline; live gate closed for a separate review commit
Completed: tracked/private disconnect proof; one-call permit consumed; canonical plus paired TTY holder enumeration and evidence binding; six-servo Torque_Enable read and trace-decoded evidence verification
Evidence: 7ea26651 remote; proof 627de4fd...; permit 85f91cea...; private a9941b84.../9b45502b...; all-alias holder b33a7cc0... counts [0,0]; census 28d087fe.../41526a67.../d58f0e8d...
Verification: 50 focused; 229 broad in 74.864 seconds; both offline runtime verifiers; fixture and disconnect-proof verifiers; py_compile; privacy scan; git diff --check
Hardware: none during Brief 043; no serial/camera open, Studio POST, reconnect, signal, write, torque change, motion, policy actuation, or training
Proof wording: disconnect evidence is honestly reconstructed; no accepted live census/camera label; sequential capture is not synchronized or policy-shadow-input-valid
Training lock: closed
Next step: separately review, commit, push, and confirm at most one fresh finite live-gate transition
```

### 2026-07-11 - Brief 042 verified; owner review hardens next live gate

```text
Current task: T16.5b
State: in_progress; Brief 042 offline verified; live gate closed
Completed: typed signed camera failure diagnostic; bounded sanitized stderr preview; full stream counts/digests; primary+cleanup preservation; atomic immutable private failure record; no success manifest/label path
Evidence: 2d1cd97; 24 dedicated tests; 40 combined census tests; 219 broad robot-lab tests; both offline verifiers; py_compile; git diff --check
Owner review: conditional continue; canonical disconnect artifact, consumed permit, all signed serial aliases, and per-servo Torque_Enable are hard prerequisites
Proof wording: sequential census then camera is finite physical camera capture only, not synchronized or policy-shadow-input-valid
Training lock: closed
Next step: Brief 043 offline implementation and review; no live reopen in this boundary
```

### 2026-07-11 - T16.5b live attempt 002 rejected; gate reclosed

```text
Current task: T16.5b
State: in_progress; live gate closed; attempt 002 rejected
Session: t16-5b-20260711-0904-cdt; discovery 7766ed1c...; contract 51467ec7...; lease 980b555c...
Reached: metadata discovery; exact contract verification; zero-holder precheck; read-only census; no-torque close; zero-holder postcheck; first exact-name camera batch
Failure: ffmpeg subprocess returned nonzero; production exception retained neither bounded stderr text nor digest, so cause is not yet mechanically classified
Cleanup: no ffmpeg process; follower disconnected/torque false; holder 4f53cda1... count 0; private bundle absent; tracked manifest absent
Proof labels: none; physical_follower_commanded=false
Training lock: closed
Next step: commit/push rejection, implement Brief 042 offline bounded diagnostic evidence, review remotely, then reconsider a new session
```

### 2026-07-11 - T16.5b live gate reopened for one fresh finite session

```text
Current task: T16.5b
State: in_progress; live gate open only for one fresh session
Prerequisites: b211562 remote; follower disconnected/torque false; holder 4f53cda1... count 0 at 09:01:09 CDT; T16.5a verified; owner present and resume authority explicit
Allowed: metadata-only discovery; five-minute owner-presence lease; exact content-addressed contract; one no-write census; two finite named-camera frames each
Mandatory guards: stable device/camera/calibration identity; zero holders before serial open and after close; handshake false; 48 allowlisted reads; disconnect disable_torque false; no configuration/torque/register writes; physical_follower_commanded=false
Withheld: proof labels until accepted evidence verifies; reconnect without no-motion proof; motion; policy actuation; physical qualification; training
Training lock: closed
Next step: commit/push this gate, confirm remote, then prepare and execute a brand-new session once
```

### 2026-07-11 - Virtual follower disconnect and zero-holder proof verified

```text
Current task: T16.5b
State: in_progress; exclusive follower ownership proven; live gate still closed
Operation: one POST /api/hardware/disconnect with {"role":"follower"}; call count 1; HTTP 200; response {"connected":false}; no retry
Postconditions: hardware d58a7549... follower disconnected/torque false; holder 4f53cda1... count 0; leader connected; safety 8c425d38... unchanged; routing 620cb845... unchanged; jobs 0
Writes: only the owner-authorized torque-disable inherent in follower disconnect; no motion, goal, leader, safety, routing, policy, or training operation
Authority gained: verified virtual follower disconnect; exclusive follower bus ownership
Authority withheld: live proof labels, motion, reconnect without no-motion proof, general register writes, physical qualification, training
Training lock: closed
Next step: commit/push this boundary; confirm remote; then separately review and open a fresh-session-only live gate
```

### 2026-07-11 - Owner-authorized virtual follower disconnect resumes T16.5b

```text
Current task: T16.5b
State: in_progress; live gate closed; prior blocked audit resolved by owner message
Completed: fresh branch/remote/dirty/status/holder revalidation; narrow disconnect plan; durable resume boundary
Evidence: 08:53:51 CDT holder 64230513... count 1; hardware 79f4ce89... follower connected/torque true; safety 8c425d38... armed; routing 620cb845... none; jobs 0
Authority: exactly one Studio follower disconnect call, including inherent torque-disable, plus response/status/zero-holder verification; later reconnect only if proven no-motion-safe
Withheld: motion command, leader disconnect, safety-route mutation, general register writes, policy actuation, physical qualification, training
Training lock: closed
Next step: commit/push this boundary; execute the exact disconnect once; fail closed unless response, status, and holder proof all agree
```

### 2026-07-11 - T16.5b blocked after third identical owner-authority audit

```text
Current task: T16.5b
State: blocked; stop sentinel active
Completed: third independent read-only holder/status audit; blocked-threshold review; durable owner choice packet
Evidence: 05:54:27 CDT holder 64230513... count 1; hardware 79f4ce89... follower connected/torque true; safety 8c425d38... armed; routing 620cb845... none; jobs 0; reviewer 054; manager 013
Blocked classification: missing_input at a proven human-authority boundary, repeated for three consecutive Goal turns
Forbidden while blocked: process signal, Studio disconnect/safety POST, serial/camera open, register write, torque change, motion, policy actuation, training
Unblock: owner manually disconnects follower, explicitly authorizes exact torque-release disconnect, or selects offline-only disposition
Training lock: closed
Next step: mark persisted Goal blocked and wait for owner choice
```

### 2026-07-11 - Studio reports torque on; disconnect choice escalated to owner

```text
Current task: T16.5b
State: in_progress; live gate closed; owner authority decision pending
Completed: read-only source audit of Studio shutdown/disconnect semantics; GET-only health/hardware/safety/routing/jobs status audit
Evidence: hardware hash 79f4ce89...; safety hash 8c425d38...; routing hash 620cb845...; follower connected true; follower torque true; safety armed true; running jobs 0; follower route none
Safety finding: SIGTERM does not call hardware disconnect/torque release; HTTP follower disconnect does release torque and is a motor-register write
Authority: neither process signal nor torque-changing endpoint was invoked
Remaining: owner manually disconnects follower, explicitly authorizes exact disconnect, or keeps Studio active and accepts offline-only continuation
Blockers: exclusive follower bus ownership cannot be established while Studio remains connected
Training lock: closed
Next step: present the exact three-way owner choice
```

### 2026-07-11 - Fresh serial-holder gate remains closed; owner decision required

```text
Current task: T16.5b
State: in_progress; live gate closed; owner decision pending
Completed: remote confirmation through c686ab6; fresh read-only holder check using the reviewed guard
Evidence: snapshot 642305133b602477840e31d756e52b11cf5d97e689eda15ae2741291ed47106c at 2026-07-11T05:47:27-05:00; holder count 1; serial device opened by check false
Authority: no process stop/signal has been performed; no force-kill authority requested or inferred
Remaining: owner choice on graceful Studio server stop; zero-holder verification; only then a separately recorded live-gate reopen decision
Blockers: one independent holder remains
Hardware state: no serial/camera open during the recheck
Training lock: closed
Next step: ask owner for narrow graceful-stop authority
```

### 2026-07-11 - Brief 041 offline correction reviewed; live gate remains closed

```text
Current task: T16.5b
State: in_progress; offline correction verified; live gate closed
Completed: stable exact-name/unique-ID camera binding; finite ffmpeg PNG batch parser; decompressed pixel/scanline validation; subprocess cleanup/evidence counts; pre-open/post-close zero-holder serial gate
Evidence: ea99ec9/66003d8/fd13bf6/01802a0; reviewer 053; 19 dedicated, 35 combined census, and 214 broad tests; both runtime offline verifiers; no hardware reopened
Authority: offline harness capabilities only; attempt 001 remains rejected; proof labels remain empty
Remaining: remote preservation; explicit owner resolution of the pre-existing Studio server; only then reconsider a new session/lease under the closed-by-default gate
Blockers: one pre-existing Studio server was last observed holding the follower serial device; capture code will now reject any holder before serial open
Hardware state: no new enumeration/open during Brief 041; historical attempt 001 remains rejected and closed
Training lock: closed
Next step: commit/push reviewer 053 and canonical state, confirm remote, then request owner direction for the independent holder while continuing offline
```

### 2026-07-11 - T16.5b live attempt 001 rejected; live gate closed

```text
Current task: T16.5b
State: in_progress offline; live gate closed
Completed: one bounded contract attempt reached post-close discovery and cleanup; failure containment; pre-existing serial holder identification; redacted camera-drift comparison
Evidence: contract 2102227c...; lease c9c9a88d...; AVFoundation camera-name set unchanged but index/name mappings swapped; Studio server started 2026-07-08 and predates attempt; reviewer 052
Accepted evidence: none; no private bundle, tracked manifest, live proof label, write, torque, motion, or physical qualification claim
Remaining: Brief 041 stable name/unique-ID-bound finite camera path; review/push; owner resolution of independent serial holder before another live open
Blockers: ephemeral numeric camera indexes; exclusive follower-bus ownership unproven
Hardware state: attempt process exited after cleanup and before evidence writing; pre-existing Studio server preserved untouched
Training lock: closed
Next step: commit/push the rejection boundary, then implement Brief 041 entirely offline
```

### 2026-07-11 - T16.5b metadata discovery and compatibility correction reviewed

```text
Current task: T16.5b
State: in_progress
Completed: metadata-only discovery; actual-OS optional-manufacturer compatibility correction; exact hashed follower/two-camera/six-joint-calibration resolution
Evidence: discovery 53440393...; follower hash 321be886...; camera-set hash 427eaa29...; calibration hash 192404b6...; correction b85a253; reviewer 051; 14 dedicated/30 combined/209 broad tests
Commit: b85a253 correction; review/canonical preservation pending
Remaining: push correction/reviewer; create short lease and exact execution contract; one bounded live read-only census/camera attempt
Blockers: none now; any remote, identity, lease, contract, source, model, telemetry, camera, or cleanup mismatch fails closed
Hardware state: metadata enumerated; serial ports opened 0; cameras opened 0; follower commanded false
Training lock: closed
Next step: commit reviewer 051 and canonical state, push/confirm the named remote, then prepare and inspect the exact private lease/contract
```

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
