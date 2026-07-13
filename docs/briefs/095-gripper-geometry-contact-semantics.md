# Slice Brief 095 - Gripper Geometry And Contact Semantics

**Date:** 2026-07-13

## Objective

Correct the compiled MuJoCo gripper/contact semantics proven weak by Briefs
091-093 before running another grasp search.

## Contract

- Emit a deterministic `GripperGeometryAudit` from the exact compiled model,
  including gripper/moving-jaw bodies, every descendant geom, names/IDs, types,
  dimensions, poses, orientations, collision masks, semantic roles, moving-jaw
  joint axis/range, aperture curve, aperture extrema, and object dimensions.
- Distinguish fixed and moving fingertip pads from palm, shell, link, mount, and
  other non-pad geometry. Non-pad contacts cannot count as jaw contact.
- If the source model lacks unambiguous collision-geom names, add explicit pad
  identities without changing the underlying collision geometry and record the
  model-version change.
- Define one canonical contact convention in object coordinates and orient each
  normal independently of MuJoCo geom ordering. Retain raw geom/body IDs and
  names, frame, position, force components, and object/tip side.
- Prove the convention with a deterministic synthetic box-and-pad fixture whose
  expected normals are analytic and whose geom ordering is exercised both ways.
- Aggregate each frame by designated pad using positive finite normal-force
  weights. Compute representative centroids, centroid span, closing-axis
  projection, normal opposition/alignment, signed center locations, force
  balance, and diagnostic pairwise span extrema.
- Produce the strict-v2 witness only from the two pad-qualified representative
  contacts. Preserve prior v1/v2 fixtures and Briefs 090-093 byte-for-byte.

This slice may establish truthful compiled geometry and contact-adapter
capabilities. It may not establish an actual grasp, training readiness,
physical calibration, transfer, qualification, or motion authority.

## Verified Outcome

- The exact compiled grasp model exposes three gripper-descendant bodies and 12
  geoms after the versioned semantic adapter.
- The original servo shell and fixed/moving composite jaw meshes remain
  unchanged and are explicitly non-pad. Two separately named active box geoms
  are the only fixed/moving fingertip pads eligible for strict witnesses.
- The simulation-only fingertip reference aperture spans 0.005237999 to
  0.130944453 m across nine deterministic gripper-qpos samples. It is not a
  physical aperture calibration.
- Canonical normals are represented in object coordinates and point inward
  toward the object. A symmetric box fixture produces identical witnesses when
  XML geom declaration order is reversed.
- Force-weighted pad centroids produce Euclidean/projected span, opposition,
  alignment, signed center location, force balance, pairwise diagnostics, and
  the strict-v2 witness. Non-pad and nonpositive/non-finite contacts fail closed.
- Artifact identity: `9bfce4c6fab67cc9259414a2c3d1615b810e2ffb00e7c00070700a64992f6c88`.
- File SHA-256: `45d74b3d3e98fb361877ed6a754b6c9fc30f87aac655bf07681ad45e45532494`.
- Four final focused tests pass in each pinned runtime; the final 174-test broad
  authority/twin/grasp gate passes.
