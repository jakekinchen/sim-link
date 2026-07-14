# SceneSmith SO-101 Program Documentation

This is the front door for the active robotics program inside the wider
SceneSmith research repository. It explains the current SO-101/MuJoCo/LeRobot
work without replacing the canonical state, signed evidence, or slice history.

## Start Here

| If you want to… | Read this first | Then follow |
| --- | --- | --- |
| Understand what is happening now | [Current state](#current-state) | [roadmap](#roadmap-and-next-work) and the active brief |
| Learn how the pieces fit together | [Architecture](./architecture.md) | [requirements and contracts](./requirements-and-contracts.md) |
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

## System At A Glance

SceneSmith provides the surrounding simulation and application context.
SO-ARM100 supplies the robot geometry/MJCF source. Pinned LeRobot supplies the
actual policy, training, processor, motor, teleoperation, and dataset APIs.
leLab is a pinned UI/runtime/URDF surface. SceneSmith-owned code is deliberately
thin: content-addressed artifacts, truthful grasp semantics, the SO-101
coordinate bridge, and fail-closed authority/stack checks.

Read [Architecture](./architecture.md) for the component, data, and authority
flows. Read [Requirements and contracts](./requirements-and-contracts.md) for
the rules those flows must satisfy.

## Roadmap And Next Work

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
