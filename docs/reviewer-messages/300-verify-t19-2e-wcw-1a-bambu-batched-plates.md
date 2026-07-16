# Reviewer 300 - ACCEPT T19.2e WCW-1A Bambu batched plates

**Date:** 2026-07-16
**Brief:** 223
**Implementation boundary:** `fb0800e1709f588e4c5740dae8bf0c53ac5af9c4`
**Decision:** ACCEPT_OFFLINE_BATCHED_PRINT_PACKAGE_AND_REPLACEMENT_DELIVERY

## Reviewed boundary

- Standard-3MF plate generator and validator:
  `scenesmith/robot_lab/wcw1a_batched_plates.py`.
- Release orchestrator: `scripts/robot_lab/build_wcw1a_release.py`.
- Batched release: `release/WCW-1A_print_package/plates/`, updated release
  documentation/validation, and
  `release/WCW-1A_AprilTag_Calibration_Cube_Print_Package.zip`.
- Frozen source geometry remains the WCW-1A-R1 boundary accepted by Reviewer
  298; this slice changes packaging and print-job arrangement only.

## Verification evidence

- The preferred 256 x 256 mm route is exactly two print jobs including the
  coupon. Its production plate contains exactly 12 independent named objects:
  one body, one lid, five carriers, and five retainers.
- The conservative 180 x 180 mm fallback is exactly four jobs including the
  coupon. Across the coupon, C1 fit pair, remaining hardware/lid, and body
  plates, every required part appears exactly once.
- All five 3MFs are CRC-valid OPC packages using the 3MF Core namespace and
  millimetre units. Content types, model relationships, object identities,
  finite vertices, triangle indices, transforms, z=0 placement, source-STL
  hashes/counts/bounds, declared-bed bounds, edge margins, and pairwise spacing
  pass. The 256 mm production plate has 10.0 mm edge margin and 10.0 mm nominal
  spacing; the densest 180 mm plate has 8.0 mm edge margin and 6.0 mm spacing.
- Canonical triangle comparison against the prior accepted release proves all
  13 STLs are geometrically identical despite nondeterministic binary triangle
  ordering in five regenerated retainer exports. Existing STL, AprilTag,
  assembly, manifest, and final-gate checks remain passing.
- Visual review covers all five projected-mesh plate maps and both Poppler-
  rendered pages of the unchanged 1:1 AprilTag PDF. Pixel bounds confirm the
  long map titles are present in the PNGs; an in-app image-view crop was not a
  file defect.
- Four batched-plate tests, five WCW-1A geometry-contract tests, four metric-
  target tests, and four T19.2 readiness tests pass. Python compilation,
  `xmllint` on every 3MF model document, archive CRC, and required-file checks
  pass.
- The replacement release manifest hashes 52 artifacts. The 5,959,684-byte
  ZIP contains 54 CRC-valid entries, includes the README and all five plates,
  and has SHA-256
  `553e8c632c5cc803d33ff17a345259f5e58513092068122c5055b2d668631540`.
- Commit `fb0800e` is preserved on `origin/codex/pi05-autolearn-loop`.
- Gmail sent a reply in the existing thread to `Zane.cooke17@gmail.com`,
  explicitly directing him to disregard the earlier ZIP. Sent message ID is
  `19f6d4d052383966`; attachments are the replacement ZIP and separate
  `README_PRINTING.md`. The first attempt failed before sending because Gmail
  required the original thread subject; no duplicate replacement was sent.

## Adversarial review

- Authority: no printer, camera, serial port, robot, optimizer, external
  compute, package installation, or Brev action occurred. The only external
  mutation was the already owner-authorized replacement email to the named
  printer.
- Evidence separation: valid 3MF/XML, mesh, and layout proof is not relabeled
  as native Bambu Studio open proof, a successful slice, a physical print,
  coupon fit, ball retention, calibration, or twin qualification.
- Geometry drift: all plate meshes are regenerated directly from the release
  STLs, rotations preserve winding, each object remains independent, and the
  fallback/primary exact-part-set tests prevent missing or double-counted
  components.
- Unsafe defaults: the 3MFs intentionally embed no printer, nozzle, material,
  or plate profile. README/QC require selecting the actual printer and 0.4 mm
  nozzle, reviewing the slice, retaining the verified arrangement, and
  printing only one route.
- Numeric and graph ambiguity: all object vertices/transforms are finite,
  build items bind one-to-one to named objects, tolerance is limited to STL
  float representation, and every bed/spacing comparison fails closed.
- Cleanup and unrelated state: commits use explicit WCW-1A paths; unrelated
  dirty configuration, external repositories, and T20 work remain untouched.

## Decision and residual risk

Accept T19.2e as a verified offline batched manufacturing package and completed
replacement delivery. Bambu Studio was not installed locally, so Zane must
select the exact printer/plate profile and confirm the native slice preview has
no model-specific exclusion-zone or out-of-bed warning. Coupon passage,
adhesion, detents, spring fatigue, shake retention, dimensions, label scale,
and mass/CoM remain physical QC. This decision opens no T19.2c live gate and
grants no printer, camera, robot, training, external-compute, or promotion
authority.
