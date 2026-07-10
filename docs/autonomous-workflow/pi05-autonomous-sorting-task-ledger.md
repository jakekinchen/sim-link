# PI0.5 Autonomous Sorting Task Ledger

Updated: 2026-07-10

## Program Status

```text
Current state: M10-M11 verified; M12 honest evaluation/provenance active
Completed: trusted data and bounded failure-focused cumulative replay
Evidence: 61 tests; strict-none eval plan; proof-contamination promotion rejection
Remaining: M12-M15 below
Blockers: none for local P0 implementation
Next step: T12.3 rotating development and locked audit seeds
```

## Tasks

| ID | Milestone | State | Task | Verification / Evidence |
|---|---|---|---|---|
| T10.1 | M10 | verified | Centralize the SO-101 MuJoCo/LeRobot transform and metadata | 28 intervention tests pass; canonical v1 contract |
| T10.2 | M10 | verified | Preserve accepted normalization or version an explicit migration | 18 tests; V10 processor equality; pinned stats hash |
| T10.3 | M10 | verified | Split correction runs at temporal/source boundaries | 20 tests; chunks cannot cross selected-frame gaps |
| T10.4 | M10 | verified | Persist the exact per-frame PI0.5 task prompt | 49 tests; legacy unlabeled DAgger frames rejected |
| T10.5 | M10 | verified | Harden dataset merge compatibility and regenerate corrections | Old corrections rejected; 12-episode/11,316-frame canary merge passes |
| T11.1 | M11 | verified | Add source- and phase-balanced sampling | 53 tests; MPS smoke realized 3 base/3 correction and all three phases |
| T11.2 | M11 | verified | Export pre-intervention and post-recovery context | Four contiguous episodes; 120 pre/90 post/660 expert frames |
| T11.3 | M11 | verified | Add pre-contact progress/stall intervention triggers | 56 tests; MPS trigger at frame 333, contact at 388, no hardware |
| T11.4 | M11 | verified | Add cumulative bounded replay registry | Bounded/hash-verified registry; duplicate trajectories rejected; merge canary passes |
| T12.1 | M12 | verified | Add stage-level reach/contact/grasp/lift/transport/release metrics | 59 tests; strict MPS smoke measured 2/4 reach/contact and 0/4 later stages |
| T12.2 | M12 | verified | Separate strict, contact-stabilized, assisted, and physical gates | 61 tests; strict gate rejects stabilized/controller/human/physical evidence |
| T12.3 | M12 | in_progress | Add rotating development and locked audit seed registries | No seed overlap or routine audit reuse |
| T12.4 | M12 | pending | Pin LeRobot/preprocessing/runtime and strengthen artifact hashes | Resume and merge verify full identities |
| T12.5 | M12 | pending | Reduce evaluation I/O and keep policy services warm | Same metrics with bounded disk/runtime |
| T13.1 | M13 | pending | Run corrected 250/500/1,000-step MPS training ladder | Reloadable checkpoints and manifests |
| T13.2 | M13 | pending | Sweep action execution horizon on paired seeds | Recorded stage/terminal comparison |
| T13.3 | M13 | pending | Run PI0.5 vs SmolVLA vs ACT/Diffusion baseline bakeoff | Same data, prompts, seeds, and proof modes |
| T13.4 | M13 | pending | Promote or reject with Git-tracked evidence | Accepted pointer changes only on verified improvement |
| T14.1 | M14 | pending | Add named curriculum randomization levels | Deterministic manifests for every level |
| T14.2 | M14 | pending | Add missing camera/dynamics/latency/calibration axes | Tests plus held-out stress tiers |
| T14.3 | M14 | pending | Add competence-gated curriculum expansion | Level advances only after configured gate |
| T15.1 | M15 | pending | Add dense progress annotations and reward-weighted BC | Offline ablation improves stage metrics |
| T15.2 | M15 | pending | Add bounded residual/action-expert RL after nonzero competence | Rollout budget, safety gate, paired evaluation |
| T15.3 | M15 | pending | Produce final capability and sim-to-real readiness audit | Honest proof matrix and remaining physical gates |

## Milestone History

### 2026-07-10 - Goal-loop rebaseline

```text
Status: M10 verified; M11 in_progress
Completed: trusted coordinate, normalization, segmentation, task, and merge contracts
Evidence: 51 tests; seed-6204 MPS canary; 660 correction frames in four contiguous episodes
Commit: 56003aa mandate; 4cd49ce T10.1; 4dfbe38 T10.2; 7468a90 T10.3; 25ddc84 T10.4; b595576 T10.5/M10
Remaining: implement M11 balanced failure-focused replay
Blockers: none
Next step: deterministic source/phase sampler with auditable exposure counts
```

### 2026-07-10 - Balanced replay sampler

```text
Status: T11.1 verified; T11.2 in_progress
Completed: content-addressed deterministic source/phase replay and realized-draw audit
Evidence: six MPS updates; 3 base/3 correction; recovery, transfer, and post-place each sampled once
Commit: d6cd8b9 T11.1
Remaining: context export, pre-contact triggers, cumulative replay registry
Blockers: none
Next step: export bounded pre-intervention and post-recovery context without crossing gaps
```

### 2026-07-10 - Temporal correction context

```text
Status: T11.2 verified; T11.3 in_progress
Completed: bounded 30-frame pre/post context with exact task and replay-role labels
Evidence: 54 tests; 870-frame context canary in four contiguous episodes; pinned merge passes
Commit: 7d7b6ee T11.2
Remaining: pre-contact triggers and cumulative replay registry
Blockers: none
Next step: deterministic approach/contact progress and stall trigger
```

### 2026-07-10 - Pre-contact stall trigger

```text
Status: T11.3 verified; T11.4 in_progress
Completed: progress-aware pre-contact stall monitor and contact-gated recovery scheduling
Evidence: 56 tests; MPS seed-6204 trigger at 333 and real contact at 388; 55 recovery frames
Commit: 6d9c2af T11.3
Remaining: cumulative bounded replay registry
Blockers: none
Next step: retain accepted correction sources across cycles under a bounded manifest
```

### 2026-07-10 - M11 bounded cumulative replay

```text
Status: M11 verified; M12 in_progress
Completed: bounded content-addressed cumulative registry and registry-driven merge/planning
Evidence: 57 tests; mutation/overlap rejection; 870-frame clean registry merge; pinned stats
Commit: 0d3a27f T11.4/M11
Remaining: M12 honest evaluation and provenance
Blockers: none
Next step: stage-level reach/contact/grasp/lift/transport/release metrics
```

### 2026-07-10 - Stage-level evaluation funnel

```text
Status: T12.1 verified; T12.2 in_progress
Completed: per-episode and aggregate reach/contact/grasp/lift/transport/release/placement metrics
Evidence: 59 tests; MPS seed-7300 strict-control smoke reached/contacted 2/4, later stages 0/4
Commit: e7d2610 T12.1
Remaining: proof modes, seed registries, provenance, evaluation runtime
Blockers: none
Next step: explicit strict/contact-stabilized/assisted/physical proof gates
```

### 2026-07-10 - Proof-mode separation

```text
Status: T12.2 verified; T12.3 in_progress
Completed: none-assist runtime and strict/contact/controller/human/physical classifiers/gates
Evidence: 61 tests; cycle eval argv uses none; stabilized success rejected by strict promotion
Commit: pending T12.2 checkpoint
Remaining: seed registries, provenance, evaluation runtime
Blockers: none
Next step: rotating development seeds and locked one-use audit seeds
```
