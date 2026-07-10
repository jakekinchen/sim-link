# Hardware Twin And Experience Compiler Goal Loop

## Mission

Build the prerequisite layer that makes later robot learning trustworthy: a
qualified SO-101 simulation contract plus an Experience Compiler that transforms
immutable raw rollouts into valid, diagnosable, reproducible training experience.

## Source Of Truth

Use these in descending authority:

1. Latest explicit user instruction and physical-safety boundary.
2. `GOAL.md`.
3. `experience-compiler-twin-task-ledger.md`.
4. `09-autonomous-milestones.md` M16-M22 and the active slice brief.
5. Machine-generated TwinProfile, compiler, mixture, and qualification artifacts.
6. Tests and current runtime evidence.
7. Earlier ledgers, session logs, and research notes.

## Intended Outcome

Given an immutable simulator or explicitly authorized robot rollout, one command
produces content-addressed frame, segment, and action-window tables; a reproducible
mixture manifest; and a training-run input manifest bound to the exact twin,
coordinate, normalization, processor, camera, prompt, reward, and environment
contracts. Raw data is never rewritten.

## Non-Goals During M16-M19

- No PI0.5, ACT, SmolVLA, or Diffusion optimizer runs.
- No residual RL.
- No physical follower instantiation, serial writes, chirps, holds, or contact tests
  without the separate authority required by M19.
- No claim of physical twin qualification from CAD or simulator-only evidence.
- No migration guessed from normalized or ambiguously ordered legacy actions.

## Acceptance Criteria

- Runtime dependencies and the structural SO-101 source are pinned by repository,
  commit, path, license, content hashes, and local patch identity.
- Twin artifacts label parameter origin (`read`, `measured`, `CAD`, or `fitted`),
  units, uncertainty, validity conditions, and evidence.
- Coordinate and gripper contracts own names, units, signs, scales, offsets,
  action representation, ranges, and safety bounds.
- Frame rows separate task phase, control mode, controller owner, source, prompt,
  policy/expert/residual/executed actions, reward components, and progress provenance.
- Segment boundaries fail closed on gaps, resets, teleports, scene/prompt/owner/
  contract changes, dropped observations, and incompatible transitions.
- Window tables for horizons 5, 10, 15, and 50 contain complete targets only,
  with no terminal padding and no hard-boundary crossing.
- Mixture manifests record configured and realized source/phase/mode draws,
  unique windows, episodes, oversampling, seed, and window-index hash.
- Full-scan, sampled-window, and twin qualification audits pass before the
  training lock can open.

## Execution Rhythm

1. Read the active ledger and latest evidence.
2. Continue its `in_progress` task; otherwise choose the lowest dependency-ready task.
3. Mark the task `in_progress` before implementation.
4. Add deterministic tests first where practical.
5. Implement without mutating raw rollouts or crossing hardware authority.
6. Run the task gate and write machine-readable evidence.
7. Update the ledger, executor log, and reviewer decision.
8. Commit only scoped files.
9. Continue only when the reviewer records `CONTINUE`.

## Stop Rules

- Stop before physical-bus access without read authority, and before commanded
  motion without separate motion authority.
- Stop before training while `training_lock: closed`.
- Stop on unknown action ordering, units, coordinate lineage, controller owner,
  prompt, or temporal semantics; quarantine rather than infer.
- Stop if a compiler change would rewrite raw rollout bytes.
- Stop if an upstream model, license, patch, or runtime cannot be pinned.
- Stop on destructive replacement, unbounded external spend, or unsafe motion.
- No privileged ownership, future progress, reward, or simulator state may leak
  into deployed actor inputs.

## Progress Record

Every loop updates:

```text
Current task:
State:
Completed:
Evidence:
Commit:
Remaining:
Blockers:
Training lock:
Next step:
```

The prerequisite loop is complete only when M16-M19 are reviewer-verified and a
machine-readable audit opens the training lock. M20-M22 then continue under the
same ledger through falsification, improvement, and honest closeout.
