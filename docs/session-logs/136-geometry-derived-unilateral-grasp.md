# Session 136 - Geometry-Derived Unilateral-Jaw Grasp

**Date:** 2026-07-13

Brief 106 replaced the stale close/height/selected-axis Halton values for
candidate 3 with controls derived from the checked geometry. The 35 mm anchor-y
width plus two 1 mm pad half-thicknesses gives a 37 mm target aperture; inverse
piecewise-linear interpolation of the verified aperture curve gives
0.2492469645 rad. Pad midpoint height is the object center and fixed-jaw
clearance is -2 mm along the selected axis, mechanically verified opposite the
fixed-to-moving closing vector.

Exact two-pass replay leaves 5.985e-9 m preclose displacement and preserves
strict-v2 bilateral pad contact for 8/8 hold, 24/24 unassisted lift, 12/12
support-free lift-hold, and 24/24 lower frames. The object rises 36.271 mm.
There are zero active-assist frames and zero non-pad robot/object contact
frames. Opening retains fixed-pad contact, which the artifact records; retreat
then clears it and ends contact-free.

Artifact `30c5873a...` verifies with file SHA-256 `d0b847e6...`. Four focused
tests pass in each configured runtime and the 198-test broad gate passes. No
hardware, inference, optimizer, training, Brev, paid compute, or physical
motion ran. Simulation training, physical qualification, and actuation remain
withheld.
