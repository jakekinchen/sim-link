# PI0.5 Autonomous Sorting Task Ledger

Updated: 2026-07-10

## Program Status

```text
Current state: M10 trusted-data gate verified; M11 replay balancing active
Completed: pipeline bootstrap, research audit, goal mandate, trusted PI0.5 data contract
Evidence: 51 tests; MPS canary; four valid correction segments; pinned stats hash
Remaining: M11-M15 below
Blockers: none for local P0 implementation
Next step: T11.1 source- and phase-balanced sampling
```

## Tasks

| ID | Milestone | State | Task | Verification / Evidence |
|---|---|---|---|---|
| T10.1 | M10 | verified | Centralize the SO-101 MuJoCo/LeRobot transform and metadata | 28 intervention tests pass; canonical v1 contract |
| T10.2 | M10 | verified | Preserve accepted normalization or version an explicit migration | 18 tests; V10 processor equality; pinned stats hash |
| T10.3 | M10 | verified | Split correction runs at temporal/source boundaries | 20 tests; chunks cannot cross selected-frame gaps |
| T10.4 | M10 | verified | Persist the exact per-frame PI0.5 task prompt | 49 tests; legacy unlabeled DAgger frames rejected |
| T10.5 | M10 | verified | Harden dataset merge compatibility and regenerate corrections | Old corrections rejected; 12-episode/11,316-frame canary merge passes |
| T11.1 | M11 | in_progress | Add source- and phase-balanced sampling | Logged sample counts match configured ratios |
| T11.2 | M11 | pending | Export pre-intervention and post-recovery context | Context windows remain temporally valid |
| T11.3 | M11 | pending | Add pre-contact progress/stall intervention triggers | Deterministic trigger tests and rollout evidence |
| T11.4 | M11 | pending | Add cumulative bounded replay registry | Prior accepted corrections retained or sampled by policy |
| T12.1 | M12 | pending | Add stage-level reach/contact/grasp/lift/transport/release metrics | Metrics emitted for baseline and candidate |
| T12.2 | M12 | pending | Separate strict, contact-stabilized, assisted, and physical gates | Promotion tests reject proof-mode contamination |
| T12.3 | M12 | pending | Add rotating development and locked audit seed registries | No seed overlap or routine audit reuse |
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
