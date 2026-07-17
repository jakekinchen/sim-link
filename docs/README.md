# SceneSmith SO-101 Program Documentation

This is the front door for the active robotics program inside the wider
SceneSmith research repository. It explains the current SO-101/MuJoCo/LeRobot
work without replacing the canonical state, signed evidence, or slice history.

## Start Here

| If you want to… | Read this first | Then follow |
| --- | --- | --- |
| Understand what is happening now | [Current state](#current-state) | [roadmap](#roadmap-and-next-work) and the active brief |
| Recreate the useful current stack in a new repository | [Portable reconstruction kit](../reconstruction-kit/README.md) | its current-state snapshot, quick start, manifest, and receipt verifier |
| Build the simplified hackathon fork | [Fork target](#fork-target-not-current-authority) | the reconstruction quick start and hackathon annex |
| Learn how the pieces fit together | [Architecture](./architecture.md) | [requirements and contracts](./requirements-and-contracts.md) |
| Connect scan or calibration work from Robo Scan | [Robo Scan integration boundary](./robo-scan-integration.md) | [integration and deduplication roadmap](./robo-scan-sim-link-integration-roadmap.md) |
| See the approved MVP cut and sim-link-only queue | [MVP execution plan](./sim-link-mvp-execution-plan.md) | `GOAL.md`, current brief, and task state |
| Run or change a safe implementation slice | [Autonomous workflow](./autonomous-workflow/README.md) | `GOAL.md`, current brief, and review decision |
| Find the authoritative rule for a capability claim | [Requirements and contracts](./requirements-and-contracts.md) | the referenced code, configuration, and test |
| Investigate an older result or rejected approach | [Current versus historical guide](./current-and-historical.md) | frozen artifact, session log, and reviewer decision |
| Evaluate an external idea or package choice | [Decisions and adjuncts](./decisions-and-adjuncts.md) | the cited adoption/rejection record |

## Current State

Read these three surfaces together; they are deliberately complementary:

1. [`../GOAL.md`](../GOAL.md) — human-readable current mission, active slice,
   and stop conditions.
2. [`autonomous-workflow/project_state.json`](./autonomous-workflow/project_state.json)
   — authoritative machine-readable task/authority state.
3. [`autonomous-workflow/experience-compiler-twin-task-ledger.md`](./autonomous-workflow/experience-compiler-twin-task-ledger.md)
   — task history, evidence summaries, and next-work routing.

Do not infer permission from a past success, a local capability, or a runtime
setting. The state file and central authority composition decide whether a
training, live-observation, physical-transfer, or promotion claim is valid.

At the current 2026-07-16 boundary, R0 source/data construction is verified and
both standard learned-policy campaigns are terminal negatives. SmolVLA ran
5,000 updates and ten rollouts without a Gate C pass. The original T20.43c
continuation remains an immutable inconclusive interruption at update 728;
T20.43c-R2 subsequently completed the unchanged ACT recipe through 10,000
updates, seven checkpoints, and fourteen rollouts. R2 had no infrastructure
failure and no Gate C pass, so ACT-on-R0 is now a verified terminal negative
rather than an unresolved capability. Its best chunk-50 behavior lifted the
cube 45.674304 mm; the final chunk-50 rollout lifted 37.655304 mm and missed
only `release_final_contact_clear`, while final receding-10 lost the grasp and
lifted 0.502 mm. No retry, learned strict-v2 success, physical qualification,
transfer, or promotion claim exists. The
[reconstruction kit current-state
snapshot](../reconstruction-kit/CURRENT_STATE.md) compresses this boundary;
`project_state.json` remains authoritative for any later change.

## Fork Target, Not Current Authority

The new-repository fork intentionally carries less machinery than this source
repo. Tonight's W1 rehearsal still proves the existing parent/child runtime and
all three retained trace schemas because that is the stack being exported. At
fork birth, the design collapses to one pinned LeRobot venv, in-process
rendering, and no subprocess dispatch layer.

The fork starts with two primary policy tracks—ACT and state-based RL. Its lower
RL rungs use camera-free joint state plus simulator object pose, light parquet,
60-frame success-terminated episodes, a frozen workcell XML, and a task
registry. Audiovisual LeRobot datasets and cameras belong to the VLA/demo tier;
SmolVLA and PI0.5 are day-three stretch work. Training may be
accelerator-nondeterministic, while the separately owned evaluator runs
CPU/fp32 and must return bit-identical verdicts across Macs and Linux.

The fork replaces the source repo's autonomous-agent ceremony with an
auto-emitted `RUN_RECEIPT.json` containing commit, config hash, dataset
identity, seed, wall clock, and metrics. It does not simplify away the frozen
held-out set, replayable signed claims, or separate evaluation ownership. All
future teleop, tests, and demo traffic use one robot gateway. Outputs are
ignored from commit one and runs have human names rather than a task alphabet.
Copied permits and reviewer artifacts remain inert history. None of this
changes current-repo authority before the morning freeze.

## System At A Glance

SceneSmith provides the surrounding simulation and application context.
SO-ARM100 supplies the robot geometry/MJCF source. Pinned LeRobot supplies the
actual policy, training, processor, motor, teleoperation, and dataset APIs.
leLab is a pinned UI/runtime/URDF surface. SceneSmith-owned code is deliberately
thin: content-addressed artifacts, truthful grasp semantics, the SO-101
coordinate bridge, and fail-closed authority/stack checks.

Robo Scan is the separate upstream modular scan/scene/calibration repository.
Its reference-only I2/I3 handoff is verified but non-authorizing. A real metric
workcell/calibration handoff and the sim-link I5 compile remain future work; a
Robo Scan checkout is not a runtime dependency and its local artifacts do not
qualify this physical twin.

Read [Architecture](./architecture.md) for the component, data, and authority
flows. Read [Requirements and contracts](./requirements-and-contracts.md) for
the rules those flows must satisfy, and [Robo Scan integration](./robo-scan-integration.md)
for the cross-repository boundary.

For the exact producer/consumer sequence, compatibility locks, ownership split,
deduplication gates, and definition of integrated, read the
[Robo Scan and sim-link integration roadmap](./robo-scan-sim-link-integration-roadmap.md).

## Roadmap And Next Work

- [Sim-link MVP execution plan](./sim-link-mvp-execution-plan.md) records the
  current product cut, dependency-ordered local queue, deferrals, and exit
  condition.
- [Portable reconstruction kit](../reconstruction-kit/README.md) records the
  evidence-pinned seed-repository boundary and the shortest honest path back to
  the same proof state.

- [Autonomous milestones](./autonomous-workflow/09-autonomous-milestones.md)
  defines M0–M22 as outcome gates.
- [Experience-compiler goal loop](./autonomous-workflow/experience-compiler-twin-goal-loop.md)
  explains the current operating loop and stop rules.
- [Task ledger](./autonomous-workflow/experience-compiler-twin-task-ledger.md)
  is the detailed work queue and proof record.

The current task may be `in_progress` while individual sub-boundaries are
verified. In that case, the task state is intentionally conservative: use its
`implementation_commits`, current brief, reviewer decision, and ledger entry
to distinguish verified slices from a completed parent task.

## Evidence, History, And Decisions

| Surface | Purpose | Treat as |
| --- | --- | --- |
| [`briefs/`](./briefs/) | Planned slice contracts and acceptance criteria | intent at a point in time |
| [`session-logs/`](./session-logs/) | What was run, changed, and observed | execution evidence |
| [`reviewer-messages/`](./reviewer-messages/) | Acceptance, redirection, and scope decisions | review authority for a slice |
| [`manager-log/`](./manager-log/) | Escalations and workflow corrections | process history |
| [`autonomous-workflow/proof-state-history.md`](./autonomous-workflow/proof-state-history.md) | Major proof-state transitions | historical interpretation |

These records are append-only context, not a second source of live authority.
Use [Current versus historical](./current-and-historical.md) before treating an
older plan, artifact, or result as active.

## Maintainer Rules

- Route to a canonical source instead of copying mutable state into a new
  explainer.
- Preserve exact evidence labels: fixture, synthetic, simulation, replay,
  physical read-only, policy evaluation, and physical proof are not
  interchangeable.
- Add a brief before a material implementation slice, then a session log and
  reviewer decision after verification.
- Update this hub when a new enduring system-level explainer, contract family,
  or current decision surface is introduced.
