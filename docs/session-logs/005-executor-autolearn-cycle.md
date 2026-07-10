# Executor Session 005 - bounded autolearn cycle

**Date:** 2026-07-10

## Slice

Add a Git-guarded PI0.5 cycle runner, compatible DAgger/base-dataset
aggregation, bounded local MPS training configuration, temporary policy-server
evaluation wrapper, and held-out promotion or rollback boundary.

## Files Changed

- `scenesmith/robot_lab/autolearn_cycle.py`
- `scripts/robot_lab/run_pi05_autolearn_cycle.py`
- `scripts/robot_lab/run_pi05_eval_with_server.py`
- `scripts/robot_lab/merge_pi05_training_datasets.py`
- `scripts/robot_lab/export_intervention_dataset.py`
- `configurations/robot_lab/pi05_autolearn.example.json`
- `experiments/pi05_autolearn/`
- `tests/unit/test_pi05_autolearn.py`

## Tests / Validation

- The combined scene-builder, intervention, and autolearn suite passed 45
  tests.
- Python compilation passed for the runner, evaluation wrapper, exporter, and
  merge utility.
- The real six-stage configuration dry-run wrote a manifest from commit
  `62519d3` without starting inference or training.
- A real data-path smoke re-exported 660 V10 controller corrections as six-axis
  PI0.5 causal data, then merged them with 10,656 base frames. The verified
  result contains 9 episodes and 11,316 frames.

## Reachability

The example configuration resolves all commands and artifacts for baseline
evaluation, assisted collection, correction export, dataset aggregation,
25-step MPS fine-tuning, candidate evaluation, and promotion. The runner
refuses dirty scoped paths and commits the manifest at every completed stage.

## Safety / Cost Boundaries

- Commands are argv arrays with per-stage timeouts; shell `-c` is rejected.
- Train and evaluation seeds must be unique, contiguous, and disjoint.
- The training command must declare the configured finite `--steps` value.
- Physical follower command markers are rejected.
- If a Brev-backed config is supplied, cleanup and final inventory run directly
  after training on both success and failure. The checked-in example uses local
  MPS and no paid external compute.

## Step-9 Flags For Reviewer

- This slice proves the automation and real dataset aggregation path, not a
  promoted candidate checkpoint.
- The first real cycle remains responsible for producing baseline and
  candidate held-out metrics and an accept/reject decision.

## Next Suggested Slice

Run `cycle-001-mps` from its clean source commit, inspect its stage manifests,
and accept or roll back the 25-step candidate using the fixed seeds 7300-7303.
