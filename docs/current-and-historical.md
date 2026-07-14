# Current Versus Historical Documentation

The repository preserves evidence rather than rewriting history. That makes old
documents valuable, but it also means age and filename alone do not establish
whether a record is active. Use this guide to read the documentation safely.

## The Current Truth Surface

Read these in order for the present program state:

1. [`../GOAL.md`](../GOAL.md) — current mission and active slice.
2. [`autonomous-workflow/project_state.json`](./autonomous-workflow/project_state.json)
   — authoritative machine-readable task and authority state.
3. [`autonomous-workflow/experience-compiler-twin-task-ledger.md`](./autonomous-workflow/experience-compiler-twin-task-ledger.md)
   — state transitions, evidence summaries, and next-work routing.
4. [Autonomous milestones](./autonomous-workflow/09-autonomous-milestones.md)
   — durable roadmap outcomes.
5. The current brief and its reviewer decision — exact implementation scope.

The project may intentionally show a parent task as `in_progress` after one or
more verified implementation boundaries. In that situation, do not read the
top-level latest-verified pointer as a contradiction: inspect the active task’s
`implementation_commits`, reviewer decision, result text, and ledger entry.

## Living Reference Guides

These are maintained explainers, not time-capsule evidence:

- [Documentation hub](./README.md)
- [Architecture](./architecture.md)
- [Sim-link MVP execution plan](./sim-link-mvp-execution-plan.md)
- [Requirements and contracts](./requirements-and-contracts.md)
- [Bespoke-versus-package recreation map](./autonomous-workflow/bespoke-package-recreation-map.md)
- [Minimal live-adapter recreation](./autonomous-workflow/minimal-live-adapter-recreation.md)
- [Robo Scan integration boundary](./robo-scan-integration.md)
- [Robo Scan and sim-link integration roadmap](./robo-scan-sim-link-integration-roadmap.md)
- [Autonomous workflow](./autonomous-workflow/README.md)

Update these when a durable boundary, ownership rule, or reader route changes.
Do not put time-sensitive task status here.

## Append-Only Evidence History

| Location | Interpretation |
| --- | --- |
| [`briefs/`](./briefs/) | Planned contract for a numbered slice; later briefs can supersede its direction. |
| [`session-logs/`](./session-logs/) | What was observed and validated in that session. |
| [`reviewer-messages/`](./reviewer-messages/) | Review decision for the exact scoped diff. |
| [`manager-log/`](./manager-log/) | Escalations and workflow interventions. |
| [`autonomous-workflow/proof-state-history.md`](./autonomous-workflow/proof-state-history.md) | Curated explanation of major transitions. |
| Signed files in `configurations/robot_lab/` | Immutable inputs/evidence; do not regenerate or edit in place. |

An older positive result is not a current permit. A retained negative result is
not a failure to ignore; it is often a guard against repeating the same mistake.

## Superseded Or Historical Routes

The following documents remain useful context but are not the default live
entry point for the current M20 clean-supervision work:

| Historical route | Why it is historical | Read it when |
| --- | --- | --- |
| [`pi05-autonomous-sorting-goal-loop.md`](./autonomous-workflow/pi05-autonomous-sorting-goal-loop.md) and its task ledger | Earlier sorting-transfer program; later work records its negative-transfer disposition. | Investigating why the current program does not reuse its checkpoint/path. |
| T19 search briefs and frozen diagnostic JSON | Retired search wrappers produced durable diagnostic evidence; the live primitive is now constructive geometry. | Auditing the grasp design decision. |
| Historical live-observation modules and briefs | Evidence is retained; the future minimal adapter is only a design contract. | Reviewing actual past live proof, never as an automatic runtime dependency. |
| A Robo Scan checkout or unsealed scan result | It is governed by the separate Robo Scan state and has no automatic sim-link authority. The accepted reference-only receipt is useful only through the pinned I2/I3 adapter. | Evaluating a future metric I4 handoff under a new reviewed sim-link brief. |
| Original SceneSmith paper README | Describes the broader research repository. | Installing or studying the paper’s scene-generation pipeline. |

## Status-Reading Checklist

Before acting on any claim, answer:

1. Is it in the current task’s state/ledger, or only in an older log?
2. What evidence mode produced it: fixture, synthetic, simulation, replay,
   physical read-only, policy evaluation, or physical proof?
3. Does the central authority composer grant the claimed next step now?
4. Is the referenced stack, source artifact, and branch identity still pinned?
5. Is a newer reviewer decision or brief narrowing or retiring it?

If any answer is unclear, stop at the narrower proof label and route through the
current state surface instead of elevating historical context.
