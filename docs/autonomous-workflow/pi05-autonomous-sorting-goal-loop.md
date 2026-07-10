# PI0.5 Autonomous Sorting Goal-Loop Mandate

## Mission

Build and verify a self-improving SceneSmith PI0.5 sorting loop that learns from
policy-visited failures, trains reproducibly on Apple MPS or bounded external
compute, promotes only genuinely better strict-policy candidates, and preserves
honest separation between neural, stabilized, assisted, and physical proof.

## Source Of Truth

Use these sources in descending order of authority:

1. The latest explicit user instruction.
2. This mandate and `GOAL.md`.
3. `pi05-autonomous-sorting-task-ledger.md`.
4. `09-autonomous-milestones.md` and the active numbered slice brief.
5. Machine-readable cycle manifests and `experiments/pi05_autolearn/accepted.json`.
6. Tests, source code, dataset/checkpoint manifests, and runtime artifacts.
7. Executor logs, reviewer decisions, and research notes.

Earlier completion claims never outrank current machine-readable evidence.

## Intended Outcome

The repository can repeatedly:

1. roll out the accepted policy on curriculum-randomized SO-101 workcells;
2. detect lack of task progress and apply clearly labeled expert corrections;
3. export temporally valid, calibrated, task-conditioned replay;
4. train bounded candidates with logged source/phase exposure;
5. evaluate baseline and candidates on paired, disjoint seed panels;
6. promote only a statistically credible strict-policy improvement;
7. roll back safely and choose the next correction or curriculum change;
8. preserve every feature, training, evaluation, and promotion boundary in Git.

## Acceptance Criteria

- One canonical, round-trip-tested SO-101 coordinate transform is used by expert
  generation, intervention export, training data, and inference.
- Dataset merges reject transform, normalization, preprocessing, feature, task,
  or temporal-contract mismatches.
- No PI0.5 action chunk crosses a source discontinuity or incompatible phase.
- Every training frame records the prompt shown to the policy, action owner,
  source phase, source episode/frame, and randomization identity.
- Training uses explicit source/phase weighting and logs actual sampled exposure.
- Correction replay includes pre-contact approach/grasp failures and is cumulative
  or deliberately reservoir-sampled across cycles.
- Evaluation reports strict policy-only, contact-stabilized, controller-assisted,
  and physical modes separately plus approach/contact/grasp/lift/transport/release
  progress metrics.
- Development and promotion seed panels are disjoint from collection seeds; a
  locked audit panel is not reused for routine model selection.
- A corrected MPS training ladder produces reloadable checkpoints and a recorded
  paired accept/reject decision without changing the accepted pointer on failure.
- Randomization expands through named competence-gated levels rather than one
  uniformly broad distribution.
- Reward-weighted learning is validated before bounded online RL; sparse terminal
  RL is not used while the strict policy produces no successful rollouts.
- All milestone changes, manifests, and decisions are committed; generated video,
  images, datasets, and weights remain external but content-addressed.
- No physical follower is opened or commanded, and no paid Brev resource remains
  running after its bounded task.

## Evidence Standard

Do not claim completion without:

- changed-file list and scoped Git commit;
- deterministic test and validation output;
- dataset/checkpoint/config hashes where applicable;
- before/after evaluation on paired seeds for behavioral claims;
- explicit proof-mode classification and known limitations;
- an updated ledger row and reviewer decision.

Pipeline reachability is not model-quality evidence. Controller-assisted success
is not autonomous success. MPS-backed execution with CPU fallback enabled is not
proof that every operator ran on Metal.

## Decision Status

### Confirmed

- The goal is automated simulation learning with domain randomization, eventual
  reward-based improvement, and Git tracking between features/training cycles.
- MPS inference and bounded LoRA optimization work on this Mac.
- The current correction aggregate must be rebuilt before meaningful training.
- The physical follower is outside the current authorization boundary.

### Recommended Defaults

- Start balanced replay at 50% correction/context and 50% accepted/base data,
  then tune from measured results.
- Use 250, 500, and 1,000-step MPS checkpoints for the first corrected ladder.
- Prove target-specific single-cube execution before learned multi-object planning.
- Use narrow-to-broad randomization and reward-weighted behavioral cloning before RL.

### Open Decisions

- External GPU use is optional until local MPS throughput or memory becomes the
  measured bottleneck; any paid compute must be bounded and cleaned up.
- Physical-robot validation requires a separate explicit authorization milestone.

## Execution Rhythm

Repeat until all acceptance criteria are met:

1. Inspect the mandate, ledger, active brief, artifacts, and Git state.
2. Choose the next smallest task that advances the active invariant milestone.
3. Implement and verify it without broadening scope.
4. Record exact evidence in the ledger and executor log.
5. Review with one decision: `CONTINUE`, `NUDGE`, `REDIRECT`, `STOP`, or `ESCALATE`.
6. Commit the verified boundary and move to the next task.

## Progress Ledger Contract

The ledger must be updated at task start and at milestone completion. Every
milestone entry records:

```text
Status:
Completed:
Evidence:
Commit:
Remaining:
Blockers:
Next step:
```

Allowed task states are `pending`, `in_progress`, `verified`, `blocked`, and
`deferred`. A milestone becomes `verified` only after its gate passes and its
reviewer decision is recorded.

## Completion Condition

Stop the goal loop only when all acceptance criteria are verified, or when a
remaining action requires new human authority. If strict autonomous sorting is
still not achieved, the loop is not complete merely because the pipeline works;
the ledger must identify the measured failure stage and the next bounded learning
experiment.
