# Slice Brief 223 - T19.2e WCW-1A Bambu batched plates

**Date:** 2026-07-16

## Objective

Replace the print-one-file-at-a-time handoff with validated batched plate files
that open as arranged multi-object projects in Bambu Studio, while preserving
the independently usable WCW-1A-R1 STLs and all frozen mechanical/tag geometry.
Rebuild, revalidate, repackage, and send the corrected release to the same
owner-named printer as an explicit replacement for the earlier attachment.

This is an offline additive-manufacturing packaging slice. It does not alter
part geometry, access a printer or robot, start training or external compute,
or prove an as-printed fit.

## Plate contract

- Generate standard unit-millimetre 3MF projects with named independent mesh
  objects and explicit build-item transforms; do not merge touching geometry.
- Primary path targets the common 256 x 256 mm Bambu A1/P1/X1-class plate:
  print the fit coupon alone, then print all 12 production parts in one arranged
  full-kit plate after the coupon passes.
- Provide a conservative 180 x 180 mm fallback for an A1 mini or unknown small
  plate: coupon, C1 carrier/retainer fit-check, remaining hardware, and body.
- Freeze at least 6 mm edge margin and 6 mm XY object spacing. Every transformed
  mesh must sit at z=0, stay within the declared bed, and retain the README's
  support-free print orientation.
- Preserve one copy each of body, lid, C0-C4 carriers, C0-C4 retainers, and
  coupon. The 256 mm full-kit plate must contain exactly the 12 production
  parts and exclude the coupon.
- Add rendered top-view plate maps, machine-readable 3MF validation, updated
  copy/job instructions, manifest hashes, and a CRC-verified replacement ZIP.

## Verification and delivery gate

- Parse every generated 3MF as OPC/XML, verify relationships/content types,
  object names, finite vertices, triangle indices, transforms, z=0 placement,
  bed bounds, spacing, part counts, and source-STL SHA-256 binding.
- Independently compare transformed 3MF bounds to the source STL bounds and
  frozen orientation rules. Reject overlap, missing/duplicate parts, or a
  plate that exceeds its declared bed.
- Visually inspect every plate map and re-render/reinspect the unchanged 1:1
  AprilTag PDF after the release rebuild.
- Re-run the STL, AprilTag, manifest, and ZIP gates. Preserve a scoped commit on
  `origin/codex/pi05-autolearn-loop` before delivery.
- Send a follow-up replacement email to `Zane.cooke17@gmail.com`, with the new
  ZIP and README attached, explicitly telling him to discard the earlier ZIP.
  Do not claim printer or slicer proof beyond the validated standard 3MF/XML
  and plate-layout checks when Bambu Studio is not installed locally.
