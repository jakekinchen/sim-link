# GOAL

## Active Mission

Complete the SceneSmith PI0.5 autonomous sorting program through a bounded,
Git-tracked goal loop. Repair the robot/data contract before further training,
then build validated intervention replay, balanced fine-tuning, stage-level
evaluation, curriculum randomization, and reward-informed improvement. Update
the task ledger at every verified milestone and continue until the acceptance
criteria in `docs/autonomous-workflow/pi05-autonomous-sorting-goal-loop.md` are
met or a genuine human-authority blocker is recorded.

The physical SO-101 follower must never be instantiated or commanded by this
path. Neural-policy, contact-stabilized, controller-assisted, and physical-robot
proof states must remain distinct.

## Current Milestone

M11 - Balanced failure-focused replay

## Current Slice

Add deterministic source- and phase-balanced sampling so each bounded training
run receives meaningful exposure to trusted base behavior and sparse correction
windows. Log actual sample counts and preserve cumulative accepted corrections.

## Durable State

- Goal-loop mandate: `docs/autonomous-workflow/pi05-autonomous-sorting-goal-loop.md`
- Incremental task ledger: `docs/autonomous-workflow/pi05-autonomous-sorting-task-ledger.md`
- Invariant milestones: `docs/autonomous-workflow/09-autonomous-milestones.md`
- Active slice brief: latest numbered file in `docs/briefs/`
- Execution evidence: `docs/session-logs/`
- Review decisions: `docs/reviewer-messages/`
- Accepted checkpoint pointer: `experiments/pi05_autolearn/accepted.json`

## Execution Mandate

1. Read the mandate, ledger, current milestone, active brief, and Git state.
2. Select the smallest useful unchecked task in the active milestone.
3. Add deterministic tests first where practical.
4. Implement only that slice and run its verification gate.
5. Update the task ledger with status, evidence, commit, and next action.
6. Write an executor log and reviewer decision.
7. Commit only scoped robotics/workflow files at the milestone boundary.
8. Continue immediately to the next ledger task unless a stop condition applies.

## Stop Conditions

- Stop before any code path opens or writes to the physical follower port.
- Stop before destructive dataset replacement without an explicit overwrite flag.
- Stop training if coordinate transforms, normalization, preprocessing, task
  labels, temporal continuity, source weighting, or dataset identity are not
  versioned and validated.
- Never promote from training seeds, incomplete evaluation, assisted completion,
  or an uncommitted learning-loop implementation.
- Never call contact-stabilized or controller-assisted success `strict pure`.
- Stop/delete paid Brev resources after a bounded training stage finishes or
  fails and record the final inventory.
- Escalate only for missing authority, external spend/credentials, destructive
  action, physical-hardware risk, or a blocker proven across three attempts.

## Current Proof State

- PI0.5 inference, five-step LoRA training, save, finalize, reload, evaluation,
  and rollback are proven on an MPS-backed runtime.
- Hybrid controller-assisted sorting is proven; strict autonomous sorting is not.
- M10 now rejects the malformed bootstrap aggregate and proves a corrected
  12-episode canary merge with exact frame tasks and pinned normalization.
- `cycle-001-mps` is interrupted and must not resume under its current recipe.
