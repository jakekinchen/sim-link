# Session 134 - Center Selected-Axis Offset

**Date:** 2026-07-13

Brief 104 removed only the horizontal target-offset projection along each
candidate's selected anchor/closing axis, retained the transverse and vertical
offsets, and reran the bounded wrist solve at the centered target. Contact
physics, remaining search inputs, evaluator, candidate count, seeds, and
holdout role stayed fixed.

Eight candidates remain horizontally feasible and six pass the motion gate.
Two retain bilateral contact through all eight hold frames. Candidate 3 reaches
20.965 mm maximum span, above the strict 20 mm minimum; candidate 2 reaches
19.915 mm. Their best normal alignment remains only 0.052 against the strict
0.8 minimum, and both bilateral candidates fail preclose motion. No strict-v2
frame or geometry-eligible candidate exists.

Artifact `7deb2826...` verifies. Twenty-two focused tests pass in each
configured runtime and the 192-test broad gate passes. No dynamic grasp,
hardware, inference, optimizer, training, Brev, paid compute, or physical
motion ran.
