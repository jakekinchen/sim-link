# Session 131 - Principal-Axis-Aligned Search

**Date:** 2026-07-13

Brief 101 replaced independent wrist-roll use with a deterministic compiled
pad-axis/object-x alignment search while preserving object yaw, wrist flex,
offsets, close targets, settling, trajectories, contact physics, evaluator,
candidate count, seeds, and holdout role.

The first run failed closed at an unnecessarily strict provisional 0.95
threshold. The corrected canonical 0.8 threshold yielded four reachable
aligned candidates at 0.806-0.886, two of which passed the approach-motion
gate. None reached the moving pad. Their closing axes retain 0.451-0.590
vertical components because wrist flex stayed fixed, leaving zero bilateral
contacts, strict-v2 frames, or geometry-eligible candidates. The holdout
remains excluded and ineligible.

Artifact `34b2a47c...` verifies. Sixteen focused tests pass in each configured
runtime and the 186-test broad gate passes. No dynamic grasp, hardware,
inference, optimizer, training, Brev, paid compute, or physical motion ran.
