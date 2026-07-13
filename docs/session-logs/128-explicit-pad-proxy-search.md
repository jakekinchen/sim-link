# Session 128 - Explicit-Pad Proxy Search

**Date:** 2026-07-13

Brief 098 reran the exact Brief 097 candidates and holdout after disabling
contact masks on the retained composite jaw meshes. The explicit pad boxes were
the only contact-active jaw geometry; friction, compliance, mass, trajectories,
ranges, seeds, evaluator, and selection stayed fixed.

Three reachable candidates produced 277 raw fixed-pad contacts with positive
normal force up to 4.337551107 N. No moving-pad contact occurred, so no bilateral
representative, strict-v2 witness, or geometry-eligible candidate exists. The
holdout remained excluded and ineligible.

The proxy path is therefore active, but the current target convention places
the gripperframe—located beside the fixed fingertip—at the object rather than
placing the midpoint between pads at the object. The next isolated correction
is pad-midpoint-relative targeting for each close target.

Artifact `015b605e...` verifies. Eight focused tests pass in each runtime and the
180-test broad gate passes. No dynamic grasp, hardware, inference, optimizer,
training, Brev, paid compute, or physical motion ran.
