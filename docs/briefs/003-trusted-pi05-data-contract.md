# Slice Brief 003 - Trusted PI0.5 Data Contract

**Date:** 2026-07-10

## Objective

Make every PI0.5 training frame use one validated SO-101 coordinate,
normalization, temporal, and language-conditioning contract before another
candidate is trained.

## Product / Project Value

The automated loop must learn from corrections rather than silently mixing
incompatible joint targets or impossible action chunks. A failed candidate after
this milestone becomes meaningful learning evidence instead of a data-pipeline
artifact.

## Acceptance Criteria

- Expert generation, intervention export, and inference share one canonical
  MuJoCo/LeRobot transform.
- Transform metadata and normalization identity are recorded and merge-checked.
- Correction exports split on temporal/source boundaries before 50-step chunks
  are built.
- Each frame retains the exact PI0.5 prompt used during collection.
- Existing malformed bootstrap data is rejected by the new validation contract.
- Unit tests cover round trips, calibrated ranges, gaps, tasks, and incompatible merges.

## Expected Files

- `scenesmith/robot_lab/so101_coordinates.py`
- `scenesmith/robot_lab/causal_sort_expert.py`
- `scripts/robot_lab/export_intervention_dataset.py`
- `scripts/robot_lab/local_policy_action_server.py`
- `scripts/robot_lab/merge_pi05_training_datasets.py`
- `tests/unit/test_robot_lab_intervention.py`
- `tests/unit/test_pi05_autolearn.py`

## Validation Commands

```bash
./.mujoco_venv/bin/python -m unittest \
  tests.unit.test_robot_lab_intervention \
  tests.unit.test_pi05_autolearn
```

## Stop Conditions

- Any required fix would command the physical follower.
- Correct transform semantics cannot be derived from the accepted runtime and dataset.
- Regeneration would destructively overwrite source evidence without an explicit flag.

## Evidence To Record

Changed files, test output, old/new action statistics, rejected malformed merge,
regenerated dataset hashes, executor log, reviewer decision, and scoped Git commit.
