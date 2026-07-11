# Slice Brief 022 - Canonical Unnamed Geom Identity V2

**Date:** 2026-07-10

## Objective

Close the remaining T16.3 semantic identity gap by making unnamed collision
keys invariant to equivalent quaternion spelling and sibling order within a
same-stem duplicate group. Do not begin T16.4 or alter hardware/training paths.

## Acceptance Criteria

- Identity hashing canonicalizes scaled and sign-equivalent explicit
  quaternions with the same semantics used by structural comparison.
- Same-stem unnamed geoms are sorted by a deterministic canonical full-
  attribute payload before occurrence suffixes are assigned.
- The secondary ordering includes normalized explicit `class`, contact, and all
  other geom attributes; canonical quaternion values are reused there.
- Reversing same-stem duplicates with different explicit friction leaves both
  collision and effective-friction records unchanged.
- Reversing same-stem duplicates attached to different classes with inherited
  friction also leaves both categories unchanged.
- Exact duplicates retain multiplicity, incompatible structures remain honest
  missing/extra evidence, and prior quaternion/contact regressions stay green.
- The artifact records identity strategy v2, is regenerated through the real
  CLI, and verifies against current source/profile hashes.

## Expected Files

- `scenesmith/robot_lab/structural_twin_diff.py`
- `tests/unit/test_structural_twin_diff.py`
- `configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json`
- One executor session log and the task ledger

## Required Tests

- Equivalent scaled/sign quaternion fixtures produce identical unnamed key sets
  and a matched collision comparison with no missing/extra records.
- Reordered same-stem explicit-friction duplicates produce byte-equivalent
  extracted collision and friction records.
- Reordered same-stem class/default-friction duplicates produce byte-equivalent
  extracted collision and friction records.
- Existing 21 structural-diff tests plus the broader robot-lab suite pass.

## Validation Commands

- `python -m unittest tests.unit.test_structural_twin_diff`
- `python -m py_compile scenesmith/robot_lab/structural_twin_diff.py tests/unit/test_structural_twin_diff.py scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py`
- `python scripts/robot_lab/write_structural_twin_diff.py --verify`
- `./.mujoco_venv/bin/python -m unittest tests.unit.test_structural_twin_diff tests.unit.test_twin_contract tests.unit.test_robotics_dependency_lock tests.unit.test_robot_lab_scene_builder`

## Exit Condition

A fresh reviewer independently reruns both adversarial fixtures and confirms the
v2 artifact is order-invariant. Only then may T16.3 close and deferred brief 021
resume as the T16.4 slice.
