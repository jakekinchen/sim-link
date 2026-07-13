# Session 130 - Post-Yaw Settle Baseline

**Date:** 2026-07-13

Brief 100 added one 0.25-second passive MuJoCo settle after object-yaw write and
readback, then anchored the preclose-motion baseline from the settled pose. It
kept the candidate design, holdout, object-relative offsets, pad-midpoint
solver, trajectories, proxy model, contact physics, evaluator, ranges, and
seeds unchanged.

Six of twelve candidates pass the 0.1 mm approach-motion gate. The two
bilateral candidates retain contact through all eight hold frames, while their
preclose displacements improve to 0.704 mm and 0.461 mm. Both remain invalid.
The best observed span is 14.713 mm against a 20 mm minimum and the best
alignment is `-0.051511158` against a 0.8 minimum, leaving zero strict-v2 valid
frames and zero geometry-eligible candidates. The holdout remains excluded and
ineligible.

Artifact `75e1ff2b...` verifies. Fourteen focused tests pass in each configured
runtime and the 184-test broad gate passes. No dynamic grasp, hardware,
inference, optimizer, training, Brev, paid compute, or physical motion ran.
