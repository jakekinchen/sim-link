# Slice Brief 002 - pi05 autolearn loop

**Date:** 2026-07-10

## Objective

Turn the current manually steered PI0.5 iteration process into a bounded,
reproducible DAgger cycle with explicit Git, data, training, evaluation,
promotion, rollback, and Brev-cleanup boundaries.

## Product / Project Value

Failed randomized policy rollouts become targeted expert corrections instead of
dead-end artifacts. A candidate checkpoint can improve only through traceable
data and can replace the accepted model only after unassisted held-out proof.

## Acceptance Criteria

- The correction exporter labels only human or privileged controller actions
  executed from policy-visited states; policy proposals remain separate.
- Train and held-out seed sets are disjoint and recorded.
- A cycle refuses dirty tracked learning-loop code by default.
- Every subprocess is an argv array with a timeout; shell strings are rejected.
- Training declares a finite step limit and, when Brev is used, a cleanup
  command that runs after success or failure.
- Candidate promotion requires a complete, assist-free held-out evaluation and
  cannot regress below the baseline success rate.
- Cycle manifests and accepted-checkpoint pointers are small Git-trackable JSON;
  datasets, model weights, observations, and rendered output remain outside Git.

## Expected Files

- `scenesmith/robot_lab/autolearn.py`
- `scripts/robot_lab/run_pi05_autolearn_cycle.py`
- `scripts/robot_lab/export_intervention_dataset.py`
- `configurations/robot_lab/pi05_autolearn.example.json`
- `tests/unit/test_pi05_autolearn.py`
- `experiments/pi05_autolearn/README.md`

## Test Plan

Use pure unit tests with temporary Git repositories and fake command runners for
cycle state, cleanup, metric parsing, promotion, and ledger behavior. Extend the
existing intervention tests for correction-frame classification. Run a dry cycle
against the real repository without launching inference or training.

## Validation Commands

```bash
./.mujoco_venv/bin/python -m unittest \
  tests.unit.test_robot_lab_scene_builder \
  tests.unit.test_robot_lab_intervention \
  tests.unit.test_pi05_autolearn

./.mujoco_venv/bin/python scripts/robot_lab/run_pi05_autolearn_cycle.py \
  --config configurations/robot_lab/pi05_autolearn.example.json --dry-run
```

## Evidence To Record

Store example/dry-run manifests under `experiments/pi05_autolearn/cycles/` and
record the commit before each feature, data, training, and promotion boundary.

## Reachability / Demo Proof

One command validates the cycle, prints each bounded stage, writes a manifest,
and exits without external compute in dry-run mode. A real config runs the same
state machine and leaves an accept/reject decision plus cleanup evidence.

## Cross-Doc Impact

Update `docs/pi05-scenesmith-recovery.md` and
`docs/so101-domain-randomized-interventions.md` with the automated loop contract.

## Out Of Scope

- End-to-end RL over the full PI0.5 backbone.
- Physical follower commands.
- Automatically pushing datasets or models to a public Hub repository.
- Committing generated observations, datasets, checkpoints, or model weights.

## Stop Conditions

- Training data cannot prove which expert action was executed.
- Any train seed overlaps the held-out evaluation set.
- A stage can run without a finite timeout or training-step limit.
- Brev cleanup cannot be verified after an external training stage.
- Promotion depends on assisted completion, an incomplete seed set, or a dirty
  learning-loop implementation.
