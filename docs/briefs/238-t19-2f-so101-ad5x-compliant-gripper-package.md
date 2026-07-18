# Slice Brief 238 - T19.2f SO-101 AD5X compliant-gripper package

**Date:** 2026-07-18

## Objective

Turn the upstream XLeRobot SO-101 split-material Fin-Ray gripper into a minimal,
printer-ready handoff for Zane's working FlashForge AD5X. Separate the two rigid
base bodies from the TPU finger, preserve the upstream support-free print
orientations, arrange each material as one ready-to-open 220 x 220 mm plate,
validate the meshes and standard 3MF containers, and send only the files and
instructions needed for two print jobs.

This is an offline additive-manufacturing packaging slice. It does not access a
printer or robot, prove an as-printed fit, change robot calibration, or grant
physical-motion, training, transfer, or promotion authority.

## Source and geometry contract

- Pin the Apache-2.0 XLeRobot source revision and preserve its combined
  `hardware/SO101_soft_fin.stl`, editable TPU-finger STEP source, license, and
  source hashes in the release provenance.
- Split the combined STL only at disconnected watertight mesh components. The
  upstream 3MF material assignment is authoritative: the 39,690-face and
  18,714-face bodies are PLA bases; the 3,480-face body is the TPU finger.
- Do not rescale, remesh, repair, smooth, decimate, or otherwise alter source
  triangles. Preserve exact per-component vertex/triangle geometry and the
  source z=0 print orientation.
- Recenter each material batch on a 220 x 220 mm AD5X bed with at least 10 mm
  edge margin. The PLA plate contains both rigid bases. The TPU plate contains
  one soft-finger body. No plate mixes materials.

## Printer and handoff contract

- Provide two standard unit-millimetre 3MF files that open as arranged build
  plates in Orca-Flashforge/Orca Slicer, plus one batch STL per plate as a
  fallback. Zane must not need to split, rotate, scale, or arrange objects.
- Target the AD5X default 0.4 mm nozzle and 0.20 mm layers. Preserve the
  upstream no-support intent. Use Zane's tuned filament temperatures and TPU
  flow/retraction because his spool formulation is not identified.
- Keep TPU as a separate single-color job and require an external/straight feed
  path rather than IFS, consistent with FlashForge's TPU-95A guidance.
- Include exact copy counts, material labels, print order, assembly ownership,
  two additional M3-screw notice, and a warning that installing the compliant
  gripper changes the physical contact geometry and therefore requires a new
  SimLink gripper calibration before calibrated robot use.

## Verification and delivery gate

- Verify each source and release STL for finite coordinates, nondegenerate
  triangles, two-incidence manifold edges, watertight boundaries, consistent
  source triangle binding, z=0 placement, bed bounds, and expected component
  count.
- Parse each 3MF as OPC/XML and verify units, relationships, content types,
  named objects, triangle indices, transforms, material separation, bed bounds,
  and exact binding to the fallback STL/source components.
- Render and visually inspect both plate layouts and every separated component.
- Generate a SHA-256 manifest, CRC-test and reopen the ZIP, perform a fresh
  same-agent adversarial review, commit and push the scoped verified boundary,
  confirm it on `origin/codex/pi05-autolearn-loop`, then email the ZIP and
  standalone README to `Zane.cooke17@gmail.com`.
- The email must say there are exactly two jobs: PLA bases, then TPU finger. It
  must not claim physical print success or compatibility with an unidentified
  TPU hardness.
