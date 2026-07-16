# Reviewer 298 - ACCEPT T19.2d WCW-1A print package

**Date:** 2026-07-16
**Brief:** 221
**Implementation boundary:** `b24ac30dbc132199baec04b80091f23fb9309b3c`
**Decision:** ACCEPT_OFFLINE_PRINT_PACKAGE_AND_DELIVERY

## Reviewed boundary

- Parametric contract: `scenesmith/robot_lab/wcw1a_spec.py`.
- Blender CAD/mesh/render generator: `scripts/robot_lab/wcw1a_cad.py`.
- Independent release/tag/STL/package validator:
  `scripts/robot_lab/build_wcw1a_release.py`.
- Release: `release/WCW-1A_print_package/` and
  `release/WCW-1A_AprilTag_Calibration_Cube_Print_Package.zip`.

## Verification evidence

- The source freezes millimetres, body frame, 40 x 60 x 65 mm bounds, C0-C4
  seats, and six-ball simultaneous inventory. Nominal ball diameter (20.0 mm)
  and diametral FDM allowance (0.8 mm) are separate parameters; the 20.8 mm
  access bore retains at least 0.6 mm diametral clearance at a 20.2 mm ball.
- Every ball installs after printing into a 45-degree conical seat and is
  captured by a separately printed sliding spring retainer with 0.20 mm
  nominal preload. Body, cartridge, retainer, and keyed bottom lid assemble and
  disassemble without trapping a ball or enclosed support.
- All 13 final binary STLs open, are outward-wound and watertight/manifold, and
  have zero boundary, non-manifold, duplicate, degenerate, or stored-normal
  errors. Blender source checks report zero self-intersection pairs for every
  component. Body bounds are exactly 40 x 60 x 65 mm.
- Analytic fit checks find no unintended interference: cartridge/body clearance
  is 0.6 mm at -x, 1.1 mm at +x, and 0.4 mm per y side; lid plug clearance is
  0.35 mm per side; retainer slide clearance is 0.20 mm. The only intended
  interferences are spring preload, removable detents, and lid crush ribs.
- Tag36h11 IDs are unique and fixed as top 0, +y 1, -y 2, +x 3, -x 4. All five
  high-resolution PNGs decode to the expected ID at Hamming 0. The two-page
  vector PDF identifies coded-square/full-label/border sizes, states Actual
  Size / 100 percent, and includes a 100.0 mm verification line.
- Fresh visual review covers the assembled cube, exploded stack, all five
  cartridges, ball-retention section, tag placement diagram, and both rendered
  PDF pages. The grasp tags remain above the central 18 mm contact band.
- Five WCW-1A contract tests, four metric-target tests, and four T19.2 readiness
  tests pass. The latter stays fail-closed on absent physical evidence.
- The release manifest hashes 40 artifacts. The 5,455,354-byte ZIP has 42
  entries, passes CRC inspection, contains the README and required artifacts,
  and has SHA-256
  `b650af2a9be918d2604ef29190f2e31c50cd8b3d7f47318528b9d01f165a6cf8`.
- Gmail sent the verified ZIP and separate README to
  `Zane.cooke17@gmail.com` with the owner-required subject. The authenticated
  sender was `jakekinchen@gmail.com`; the sent message/thread ID is
  `19f6d356a4121193`.

## Adversarial review

- Authority: no camera, serial, robot, physical motion, optimizer, network
  package installation, external compute, or Brev action occurred. Email was
  exactly the owner-authorized delivery to the named recipient.
- Evidence separation: fixture/render/mesh proof is not relabeled as a printed
  part, physical fit, metrology, calibration, or twin qualification.
- Stale references and ambiguity: the historical concept is pinned to commit
  `aec1056`; the new body/cartridge coordinate equivalence is explicit; source,
  release, manifest, ZIP, and email attachment paths are exact.
- Unsafe defaults and non-finite values: units and dimensions are frozen,
  ordinary-ball tolerance is explicit, tests tolerate only floating-point
  representation error, and all parsed mesh bounds/volumes/mass terms are
  finite and positive.
- Evidence spoofing and geometry ambiguity: exported STL parsing is independent
  of Blender's mesh statistics; source BVH and exported topology checks agree;
  pairwise mass comparisons avoid double-counting common body/lid components.
- Cleanup and unrelated state: atomic release replacement is restricted to the
  exact generated directory, intermediates are excluded, and unrelated dirty
  configuration/external repositories remain untouched.

## Decision and residual risk

Accept T19.2d as a verified offline manufacturing package and completed email
delivery. Physical proof remains deliberately open: Zane must print the coupon
first, confirm cooled ball passage, inspect detents/springs and shake retention,
measure finished dimensions and the PDF scale line, decode applied tags, and
weigh the actual balls/assemblies before their mass or CoM is treated as
metrology truth. This decision grants no T19.2c live gate or robot authority.
