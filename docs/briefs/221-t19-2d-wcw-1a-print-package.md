# Slice Brief 221 - T19.2d WCW-1A Print Package

**Date:** 2026-07-16

## Objective

Turn the historical WCW-1 mass-properties concept at commit `aec1056` into a
complete, offline-generated, printer-ready WCW-1A AprilTag calibration cube
package. The package must include corrected parametric source, watertight STL
parts, exact-size tag artwork, renders, assembly/printing instructions,
machine-readable validation, hashes, a verified ZIP, and delivery to the
owner-named printer by the strongest available email mechanism.

This is an offline design and artifact slice. It does not print a part, inspect
an as-built part, access a camera or robot, or grant calibration, physical-twin,
transfer, policy, promotion, external-compute, or Brev authority. The existing
top-level T20.44 training task and its one-use authority are not modified.

## Frozen mechanical contract

- Body frame origin is the outer-body centroid: `x` spans the 40 mm grasp
  thickness, `y` spans the 60 mm non-grasp width, and `z` spans the 65 mm
  height. Cartridge and body `y=0` coincide, so C0-C4 coordinates are body-frame
  coordinates as well as cartridge-local coordinates.
- Outer body is 40 x 60 x 65 mm before small edge chamfers. The central 18 mm
  band on both x faces remains plain and repeatable for grasping.
- The insert is removable through a mechanically possible bottom access path;
  the body, bottom retainer, cartridge, and ball retainer must be independently
  printable and reversibly assembled without trapped support or sealed balls.
- Cartridges C0-C4 retain the historical conditions: C0 empty; C1 one ball at
  y=0 mm; C2 one ball at y=+15 mm; C3 two balls at y=+/-11 mm; C4 two balls at
  y=+/-15 mm. Six balls are required to populate all five cartridges at once.
- Ball geometry is parameterized from nominal 20.0 mm ordinary commercial
  bearing balls. No grade, supplier, or sub-0.1 mm diameter premise is allowed.
  The main pocket and compliant retention system must accept an explicitly
  documented ordinary-ball tolerance range and normal FDM error without rattle
  or escape; a multi-clearance fit coupon is included.
- Cartridges and the bottom retainer are asymmetrically keyed, visibly or
  tactually identified, and retained against robot-motion translation.
- Primary print recommendation is matte white/light-gray PLA or PLA+ with a
  0.4 mm nozzle. All required copy counts, orientations, layer/wall settings,
  supports, and assembly checks are frozen in the generated README.

## AprilTag contract

- AprilTag family is `tag36h11`; IDs are unique: top 0, +y 1, -y 2, +x 3,
  and -x 4.
- Top and non-grasp labels use a 24.0 mm black coded square with a one-module
  white border, for a 30.0 mm full label. Grasp-face labels use a 16.0 mm black
  coded square and 20.0 mm full label, entirely above the contact band.
- The package distinguishes black coded-square size, full printed label size,
  white border, placement, and face-up direction. Vector PDF and high-resolution
  PNG files must state and preserve 1:1 / 100 percent printing.
- Tags remain printed labels, not FDM black/white geometry.

## Verification and release gate

- Build all release artifacts from tracked source using only
  already-available local Blender/Python/Poppler tooling.
- Reject missing, unreadable, open, non-manifold, degenerate, inverted, or
  dimensionally incorrect STL meshes. Record vertices, faces, bounds, volume,
  PLA mass estimate, pairwise assembly clearances/interference checks, assembled
  mass, and center-of-mass results for C0-C4.
- Render and visually inspect an assembly, exploded view, every cartridge, tag
  placement, and a ball-retention section. Render the final PDF through Poppler
  and verify the intended tag IDs from canonical local family data.
- Open the final ZIP and verify its exact manifest before any email action.
- Email is authorized only for the verified package to
  `Zane.cooke17@gmail.com` with subject
  `WCW-1A AprilTag calibration cube — final STL print package`. No package
  download, hardware, camera, serial, robot, paid compute, external compute, or
  Brev action is authorized.
