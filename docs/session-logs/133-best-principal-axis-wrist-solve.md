# Session 133 - Best Principal-Axis Wrist Solve

**Date:** 2026-07-13

Brief 103 applied the unchanged bounded wrist solve to both anchor principal
axes. It preserved object yaw, offsets, close target, settling, trajectories,
contact physics, evaluator, candidate count, seeds, and holdout role.

Eight candidates pass the horizontal gate, all on object y; six pass the
approach-motion gate. Candidates 2 and 3 produce bilateral explicit-pad
contact through all eight hold frames. Candidate 3 reaches 17.398 mm span
against the strict 20 mm minimum, while the best contact-normal alignment is
0.056 against the strict 0.8 minimum. Both bilateral candidates also exceed
the motion limit. No strict-v2 frame or geometry-eligible candidate exists.

Artifact `06bc0f4a...` verifies. Twenty focused tests pass in each configured
runtime and the 190-test broad gate passes. No dynamic grasp, hardware,
inference, optimizer, training, Brev, paid compute, or physical motion ran.
