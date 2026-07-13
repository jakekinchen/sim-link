# Session 125 - Gripper Geometry And Contact Semantics

**Date:** 2026-07-13

Brief 095 replaces body-name contact qualification with a versioned compiled-
model semantic adapter. The exact grasp model contains a gripper servo-shell
collision and composite fixed/moving jaw meshes. Those original collisions are
preserved and explicitly classified non-pad. Two active box geoms at the pinned
Menagerie fingertip locations are the only fixed/moving pads eligible for a
strict witness.

The deterministic audit records three gripper-descendant bodies, all 12 geoms,
their names/IDs/types/dimensions/local and world poses/orientations/collision
masks/roles, the gripper joint axis and range, and nine aperture samples. The
simulation reference aperture spans 5.237999 to 130.944453 mm; the nominal
30-50 mm object dimensions fit the maximum reference aperture, but no physical
aperture claim is made.

Contact extraction retains raw geom/body identities, frame, position, normal
and tangential forces, and object/tip side. It transforms points and normals to
object coordinates, orients normals inward toward the object independent of
geom ordering, drops non-finite/nonpositive force, and admits only explicit pad
geoms. Force-weighted representatives produce the strict-v2 witness plus all
requested span, alignment, center-location, force-balance, and pairwise
diagnostics.

The final artifact is `9bfce4c6...` with file SHA-256 `45d74b3d...`. Four
focused tests pass in each pinned runtime, the deterministic writer verifies,
and the final 174-test broad authority/twin/grasp gate passes. No hardware,
inference, optimizer, training, Brev, paid compute, or physical motion ran.
