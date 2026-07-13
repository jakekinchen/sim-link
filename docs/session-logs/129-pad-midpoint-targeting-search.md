# Session 129 - Pad-Midpoint Targeting Search

**Date:** 2026-07-13

Brief 099 reran the exact Brief 098 design after solving each arm pose against
the predicted midpoint between the fixed and moving explicit pads. Candidate
design, holdout, proxy model, friction, compliance, mass, trajectories, ranges,
seeds, evaluator, and selection remained fixed.

Two of twelve candidates produced bilateral explicit-pad contact through all
eight hold frames. Candidate 1 produced three bilateral close frames, 5.796-
7.695 mm representative spans, and best alignment `-0.279906875`. Candidate 3
produced five bilateral close frames, 8.167-14.425 mm spans, and best alignment
`-0.053688997`. Both produced zero strict-v2 valid hold frames and failed the
preclose motion gate at 8.474 mm and 2.101 mm displacement. The excluded
holdout remained excluded and ineligible.

Artifact `d18db60c...` verifies. Twelve focused tests pass in each configured
runtime and the 182-test broad gate passes. No dynamic grasp, hardware,
inference, optimizer, training, Brev, paid compute, or physical motion ran.
