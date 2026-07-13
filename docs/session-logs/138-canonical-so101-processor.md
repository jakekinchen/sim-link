# Session 138 - Canonical SO-101 Processor

**Date:** 2026-07-13

Brief 108 adds `scenesmith_so101_canonical_processor_v1` with one fixed six-joint
order and explicit absolute action mode. MuJoCo radians/gripper radians convert
bidirectionally to canonical LeRobot degrees/gripper percent without clamping.
Range validation and safety limiting are distinct operations; limiting retains
the unmodified request and reports executed values, clipped indices/names, and
whether projection occurred.

The signed artifact binds T17.1 and the SO-101 coordinate identity. Across 128
seeded in-range samples, maximum round-trip error is 4.441e-16. The golden pose
matches the legacy in-range adapter, gripper mapping is monotonic, and a 120%
request proves transform/validation/limiting separation.

Artifact `9800c873...` verifies with file SHA-256 `cd60dce9...`. Eleven focused
tests pass in each configured runtime and the 221-test broad gate passes. No
normalization bundle, compiled training frame, hardware access, optimizer,
training, Brev, paid compute, or physical motion occurred. The training lock
remains closed.
