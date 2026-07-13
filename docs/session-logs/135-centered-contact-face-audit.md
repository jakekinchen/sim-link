# Session 135 - Centered Contact-Face Audit

**Date:** 2026-07-13

Brief 105 reran only centered candidates 2 and 3 with source-identical metrics
and retained 15 bilateral close/hold aggregates per candidate. It classified
representative centroids against the analytic anchor faces without altering or
relabeling MuJoCo normals.

The fixed pad contacts the anchor `+z` top face in all 30 aggregates with
inward normal `[0, 0, -1]`. The moving pad contacts the `-y` side in 27 and the
top in three, dominantly with inward normal `[0, 1, 0]`. The bound synthetic
convention proof remains valid and geom-order independent. The failure is a
real top-face/side-face trajectory condition, not a sign-convention defect.

Artifact `23572851...` verifies. Twenty-four focused tests pass in each
configured runtime and the 194-test broad gate passes. No dynamic grasp,
hardware, inference, optimizer, training, Brev, paid compute, or physical
motion ran.
