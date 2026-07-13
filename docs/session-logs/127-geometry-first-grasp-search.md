# Session 127 - Geometry-First Grasp Search

**Date:** 2026-07-13

Brief 097 ran 12 deterministic seven-dimensional Halton training candidates and
one untouched holdout over bounded wrist flex/roll, object yaw, x/y/z offsets,
and close target. Friction, compliance, mass, solver time constants, and object
geometry remained fixed.

Ten training candidates and the holdout passed fixed-wrist pose setup; two
rejected on reachability. No candidate produced a single explicit-pad contact
frame, so none could produce a representative witness or pass strict v2. Five
reachable training candidates contacted only the preserved fixed/moving
composite jaw meshes; five made no robot-object contact. The excluded holdout
also contacted composite non-pad geometry only.

This is a precise geometry failure, not evidence to broaden friction or search
ranges. The original composite mesh collision surfaces occlude the added pad
boxes. The next one-factor correction is a versioned contact-mask change that
retains those meshes for audit but makes only explicit pads contact-active.

Artifact `bbba9eac...` verifies exactly. Twelve focused tests pass in each
pinned runtime and the 178-test broad gate passes. No lift, dynamic grasp,
hardware, inference, optimizer, training, Brev, paid compute, or motion ran.
