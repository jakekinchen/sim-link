# Executor Session 007 - Canonical SO-101 Coordinates

**Date:** 2026-07-10

## Slice

Complete T10.1 by replacing duplicated expert/export/runtime conversions with
one versioned SO-101 coordinate contract.

## Result

- Added `scenesmith.robot_lab.so101_coordinates` with canonical signs, offsets,
  gripper range, MuJoCo limits, conversion functions, and JSON metadata.
- Causal demonstration generation, intervention export, and the local PI0.5
  policy server now call the same conversion implementation.
- Correction export summaries now record the coordinate contract.
- The evaluation launcher derives server calibration arguments from the same constants.

## Verification

```text
./.mujoco_venv/bin/python -m unittest tests.unit.test_robot_lab_intervention
Ran 28 tests in 0.096s - OK
```

`git diff --check` and Python compilation also pass for the changed files.

## Proof Boundary

The code contract is repaired and unit-tested. Existing bootstrap correction
Parquet remains malformed and must be regenerated after the remaining M10 gates.

## Next Step

T10.2: keep accepted normalization stable across an incremental DAgger candidate
or make normalization migration an explicit separately evaluated boundary.
