# Session 123 - Antipodal Contact Gate

**Date:** 2026-07-13

Brief 093 implements a separately versioned v2 strict-grasp contact gate after
Brief 092 disproved named-body contact count as a force-closure proxy. V1 remains
byte-identical at `4f0bad3c...`.

The v2 witness requires two distinct jaws, two finite metric contact points, at
least 20 mm span, unit-normal opposition with dot at most -0.8, and at least 0.8
alignment of each inward normal with the contact axis. This is explicitly an
antipodal two-jaw proxy, not full 6D wrench closure or physical calibration.

One declared analytic positive passes semantic expert success but remains
non-policy. Seventeen negatives run through the same evaluator and fail for
their expected reasons. Contact-specific cases include Brief 092's exact
4.907838 mm collapsed span, missing witness, same jaw, same-side normals,
opposing but misaligned normals, malformed values, and non-finite points.

Artifact `950e7568...` is signed and deterministic. Eleven focused tests pass in
each repository runtime. No MuJoCo grasp, hardware, physical motion, inference,
optimizer, training, Brev, paid compute, or network was used.
