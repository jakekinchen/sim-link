# SceneSmith SO-101 Autonomous Workflow

## Execution identity and source of truth

- Work as one agent in the current top-level thread. Never spawn, delegate to,
  request, or use subagents. A reviewer pass is performed by the same agent.
- Treat `docs/autonomous-workflow/project_state.json` as the authoritative
  dynamic project state. Resolve contradictions there before continuing work.
- Work only on `codex/pi05-autolearn-loop` and push scoped verified commits only
  to `origin/codex/pi05-autolearn-loop`.
- At the start of every session and commit boundary, verify the branch, HEAD,
  upstream, and dirty paths. Preserve all unrelated dirty files and saved
  dirty-worktree evidence. Stage explicit paths; never use broad staging.

## Authority and proof boundaries

- Keep `training_lock` closed unless the central authority composer
  mechanically grants `simulation_training_ready` and the implementation,
  tests, review decision, project state, commit, and remote branch all agree.
- Component artifacts expose local capabilities and evidence only. They must
  not grant whole-system states such as `physical_twin_qualified`,
  `physical_transfer_ready`, or `promotion_eligible`.
- Every system-level authority decision must come through the central composer
  defined by T16.2b-A and must fail closed on missing, stale, contradictory,
  synthetic-only, fixture-only, or unauthorized evidence.
- Keep fixture, synthetic, simulation, replay, physical, and policy-evaluation
  evidence distinct. Never relabel one as another.
- Keep MPS inference, scripted/controller-assisted completion, autonomous
  closed-loop policy success, and physical-robot proof distinct.

## Prohibited actions without new owner authority

- Do not access a serial port, camera, leader, follower, servo bus, or other
  physical robot hardware. Do not instantiate a live hardware object.
- Do not run optimizer training while `training_lock` is closed.
- Do not start paid or external compute, including Brev.
- Do not merge, rebase shared history, force-push, open or merge a pull request,
  delete branches, modify repository permissions, or perform destructive data
  operations.
- Do not overwrite user data, unrelated dirty files, saved worktree evidence,
  model checkpoints, or datasets.

## Slice workflow

- Read only the highest-value current context named by `GOAL.md` and the active
  goal-loop prompt. Open older records only when a current contract or test
  depends on them.
- Before significant implementation, set the active task `in_progress` in
  `project_state.json` and write or amend the smallest precise slice brief.
- Add deterministic tests first where practical, implement one coherent slice,
  run focused tests, then the relevant broad regression gate.
- Perform a fresh same-agent adversarial review of the complete scoped diff.
  Check authority escalation, stale references, unsafe defaults, non-finite
  values, evidence spoofing, graph ambiguity, double counting, path aliasing,
  cleanup side effects, nondeterminism, and documentation contradictions.
- Update only the canonical state, active ledger, necessary session log, and
  reviewer decision. Commit and push the verified boundary, confirm the remote
  contains it, then continue to the next dependency-ready safe task.
- Never describe a slice as verified until implementation, tests, review,
  documentation, scoped commit, and remote preservation agree.

## Brev cost control

- Starting Brev is outside the current authority boundary.
- If later explicit authority permits Brev, check `brev ls` before closeout and
  stop or delete every instance no longer needed for a current verified task.
- If Brev cleanup is blocked by auth or tooling, report the blocker immediately
  and continue trying available authenticated cleanup routes. Never silently
  leave paid resources running.
