# Session 303 - T19.2e WCW-1A Bambu batched plates

**Date:** 2026-07-16
**Brief:** 223
**Reviewer:** 300

- Added five standard unit-millimetre 3MF plates with independent named mesh
  objects, frozen support-free orientations, explicit build translations, and
  rendered top-view maps.
- The preferred 256 mm Bambu route is coupon plus one 12-object production
  plate: two print jobs total. The 180 mm fallback is coupon, C1 fit pair,
  remaining hardware/lid, and body: four jobs total.
- Programmatic validation passed OPC/XML structure, CRC, object identity,
  source-STL binding, finite vertices, triangle indices, z=0, bed bounds,
  spacing/margins, exact part inventory, manifest, and ZIP gates. Canonical
  triangle comparison found all 13 production/coupon STLs geometrically
  identical to the Reviewer 298 release.
- Passed four batched-plate, five WCW-1A contract, four metric-target, and four
  readiness tests. Re-rendered and visually reviewed both AprilTag PDF pages
  and all five plate maps.
- Replacement ZIP SHA-256 is
  `553e8c632c5cc803d33ff17a345259f5e58513092068122c5055b2d668631540`;
  size is 5,959,684 bytes with 54 CRC-valid entries and 52 manifest artifacts.
- Implementation commit `fb0800e` is exact on
  `origin/codex/pi05-autolearn-loop`.
- Gmail sent the replacement ZIP and separate `README_PRINTING.md` from
  `jakekinchen@gmail.com` to `Zane.cooke17@gmail.com` under the original thread
  subject `WCW-1A AprilTag calibration cube — final STL print package`. Sent
  message ID is `19f6d4d052383966`; the body says to disregard the earlier ZIP.
- Bambu Studio was unavailable locally, so native slicer-open/slice proof is
  not claimed. No physical hardware, printer, camera, serial port, robot,
  training, external compute, or Brev resource was used.
