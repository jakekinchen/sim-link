# PI0.5 Autonomous Sorting Task Ledger

Updated: 2026-07-10

## Program Status

```text
Current state: research complete; unsafe production recipe stopped
Completed: pipeline bootstrap, research audit, goal mandate, canonical coordinate contract
Evidence: cycle manifests; 28 passing intervention tests
Remaining: M10-M15 below
Blockers: none for local P0 implementation
Next step: T10.2 accepted normalization contract
```

## Tasks

| ID | Milestone | State | Task | Verification / Evidence |
|---|---|---|---|---|
| T10.1 | M10 | verified | Centralize the SO-101 MuJoCo/LeRobot transform and metadata | 28 intervention tests pass; canonical v1 contract |
| T10.2 | M10 | in_progress | Preserve accepted normalization or version an explicit migration | Hash equality/equivalence test |
| T10.3 | M10 | pending | Split correction runs at temporal/source boundaries | No 50-step chunk crosses a gap |
| T10.4 | M10 | pending | Persist the exact per-frame PI0.5 task prompt | Exported task counts match source phases |
| T10.5 | M10 | pending | Harden dataset merge compatibility and regenerate corrections | Merge refuses incompatible contracts; regenerated stats pass |
| T11.1 | M11 | pending | Add source- and phase-balanced sampling | Logged sample counts match configured ratios |
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
Status: in_progress
Completed: goal-loop mandate and T10.1 canonical coordinate contract
Evidence: 28 intervention tests; shared transform used by expert, exporter, and server
Commit: 56003aa mandate; T10.1 implementation pending commit
Remaining: implement and verify T10.2-T10.5
Blockers: none
Next step: pin or explicitly version normalization during incremental training
```
