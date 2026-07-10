# Reviewer Decision 026 - Missing Menagerie Sources Escalation

**Date:** 2026-07-10

## Decision

`ESCALATE`

## Evidence Reviewed

- `GOAL.md`
- `docs/briefs/011-structural-twin-diff.md`
- `docs/session-logs/029-executor-structural-twin-diff-blocked.md`
- `docs/autonomous-workflow/03-planning-system.md`
- `docs/autonomous-workflow/04-execution-protocol.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- `configurations/robot_lab/pi05_robotics_dependency_lock.json`
- Latest commit `b1518d1`
- Current `git status --short`
- Current `git diff --stat`
- `find external -maxdepth 4 \( -name 'so101.xml' -o -name 'scene.xml' -o -path '*robotstudio_so101*' \) | sort`

## Findings

- `100`: Brief 011 requires a real CLI that resolves both compared models from repo state and emits a checked-in structural diff artifact, with a stop condition if the source files named by the dependency lock cannot be read. The lock records Menagerie only as remote-pinned reference files at `robotstudio_so101/so101.xml` and `robotstudio_so101/scene.xml`, not as readable local repo paths, so the requested slice is currently unreachable without an external source injection or a human-approved brief change.
- `100`: The executor's blocker claim is corroborated by repo evidence. The task ledger already marks T16.3 blocked on missing local Menagerie structural sources, and session log 029 records that repo search finds no local `robotstudio_so101` source tree while the active Robot Studio runtime MJCF is present locally.
- `50`: The worktree still contains a large unrelated unstaged product diff outside robot-lab scope. That does not change the T16.3 decision, but it remains out of bounds for this reviewer turn.

## Routing

- Treat commit `b1518d1` as a truthful blocked checkpoint for T16.3.
- Keep M16 and the current slice unchanged; do not issue a new executor brief until the missing Menagerie source prerequisite is resolved.
- Route this blocker to the Manager / human because continuing now would require either supplying new external source files to repo state or changing the acceptance contract for brief 011.

## Next Action

Obtain one explicit resolution before another executor slice starts:

1. Provide the pinned Menagerie `robotstudio_so101` source files in repo state under a tracked path that the dependency lock can reference, then resume brief 011 unchanged.
2. Or intentionally revise the brief and milestone contract if the project owner wants a different evidence model than offline repo-state diff generation.

## Manager / Human Escalation

- Evidence anchor `100`: [docs/briefs/011-structural-twin-diff.md](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/docs/briefs/011-structural-twin-diff.md:20) requires the diff artifact to compare the active runtime against pinned Menagerie source files from repo state, and its stop condition says to stop when those source files cannot be read from the lock inputs at [docs/briefs/011-structural-twin-diff.md](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/docs/briefs/011-structural-twin-diff.md:97).
- Evidence anchor `100`: [configurations/robot_lab/pi05_robotics_dependency_lock.json](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/configurations/robot_lab/pi05_robotics_dependency_lock.json:121) records Menagerie as remote-pinned reference files only, including [robotstudio_so101/so101.xml](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/configurations/robot_lab/pi05_robotics_dependency_lock.json:136) and [robotstudio_so101/scene.xml](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/configurations/robot_lab/pi05_robotics_dependency_lock.json:141), while [docs/session-logs/029-executor-structural-twin-diff-blocked.md](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/docs/session-logs/029-executor-structural-twin-diff-blocked.md:35) documents there is no corresponding local tracked source tree to open.
- Evidence anchor `100`: [docs/autonomous-workflow/experience-compiler-twin-task-ledger.md](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/docs/autonomous-workflow/experience-compiler-twin-task-ledger.md:12) and [docs/autonomous-workflow/experience-compiler-twin-task-ledger.md](/Users/kelly/Documents/Codex/2026-07-06/download-the-code-from-here-install/scenesmith/docs/autonomous-workflow/experience-compiler-twin-task-ledger.md:34) already record this as the active blocker for T16.3, so another executor implementation turn would just repeat the same impasse.
