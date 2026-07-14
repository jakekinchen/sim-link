# Document and Artifact Map

## Current Docs

| Path | Owns |
|---|---|
| `GOAL.md` | Active mission, current slice, stop sentinel, human constraints. |
| `docs/README.md` | Documentation front door and reader routing. |
| `docs/architecture.md` | Component, data-flow, tech-stack, and authority overview. |
| `docs/requirements-and-contracts.md` | Requirement families, claim vocabulary, and canonical contract routing. |
| `docs/current-and-historical.md` | Current truth surface versus append-only/historical evidence guidance. |
| `docs/decisions-and-adjuncts.md` | Package, external-pattern, and design decision index. |
| `docs/robo-scan-integration.md` | Separate Robo Scan scan/scene/calibration handoff boundary and authority limits. |
| `docs/robo-scan-sim-link-integration-roadmap.md` | Cross-repository ownership, phase gates, compatibility protocol, deduplication, and rollback plan. |
| `executor-reviewer-pair-programming.md` | Root quickstart and role overview for the pair. |
| `docs/autonomous-workflow/` | Autonomous workflow strategy and protocols. |
| `docs/autonomous-workflow/09-autonomous-milestones.md` | Invariant milestone gates. |

## Target Workflow Artifacts

| Path | Created When | Owns |
|---|---|---|
| `docs/briefs/NNN-*.md` | Before each implementation slice | Slice objective, acceptance criteria, tests, validation, expected evidence. |
| `docs/session-logs/NNN-executor-*.md` | After each Executor slice | Evidence of what changed and how it was validated. |
| `docs/session-logs/NNN-review-*.md` | After a substantial Reviewer audit | Review evidence and decision rationale. |
| `docs/reviewer-messages/NNN-*.md` | Every Reviewer decision | `CONTINUE`, `NUDGE`, `REDIRECT`, `STOP`, or `ESCALATE`. |
| `docs/manager-log/NNN-*.md` | Manager intervention | False blocker challenges, user escalation, context cycle, process optimization. |

## Single Source Of Truth By Concern

| Concern | Source |
|---|---|
| Product intent | `docs/README.md` plus `GOAL.md` and the active milestone/task sources it routes to |
| Architecture | `docs/architecture.md` |
| Tech stack / package ownership | `docs/architecture.md` plus `docs/autonomous-workflow/bespoke-package-recreation-map.md` |
| Robo Scan handoff | `docs/robo-scan-integration.md` plus the upstream repository's current state |
| Robo Scan/sim-link integration sequence | `docs/robo-scan-sim-link-integration-roadmap.md` |
| Requirements and contracts | `docs/requirements-and-contracts.md` plus referenced implementation/configuration |
| Current versus historical interpretation | `docs/current-and-historical.md` |
| External ideas and adjunct decisions | `docs/decisions-and-adjuncts.md` |
| Build order | `docs/autonomous-workflow/09-autonomous-milestones.md` plus latest brief |
| Active work | `GOAL.md` plus latest brief |
| Completed evidence | `docs/session-logs/` plus commits |
| Review decisions | `docs/reviewer-messages/` |
| Manager interventions | `docs/manager-log/` |

If a new doc duplicates one of these concerns, delete or merge it before it drifts.
