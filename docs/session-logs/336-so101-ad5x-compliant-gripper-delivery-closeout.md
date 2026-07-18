# Session 336 - SO-101 AD5X Compliant-Gripper Delivery Closeout

## Boundaries

- Branch: `codex/pi05-autolearn-loop`
- Activation: `06eade08ee54d91a8eb8d70ba95b8dc8a7ae9d6d`
- Reviewed implementation: `a309b71346423f3863629e8cd351ca37f69a6304`
- Pre-delivery review: Reviewer 331 at remote commit
  `930104ddac9a4d2ea24fd41c819144b166d94f19`
- Brief: `docs/briefs/238-t19-2f-so101-ad5x-compliant-gripper-package.md`
- No printer, camera, serial port, robot, model, optimizer, training, external
  compute, or Brev resource was accessed.

## Printer handoff

The XLeRobot SO-101 compliant gripper is packaged as exactly two AD5X jobs:

1. `SO101_R1_AD5X_plate01_PLA_gripper-bases.3mf` contains both rigid bodies.
2. `SO101_R1_AD5X_plate02_TPU95A_soft-fin.3mf` contains the complete compliant
   Fin-Ray finger.

Both jobs preserve the upstream z=0 orientation and geometry, are centered on
the 220 x 220 mm bed, and include already-arranged batch-STL fallbacks. Zane
does not need to split, rotate, scale, orient, or place individual components.
He is asked only to select his normal PLA profile and tuned TPU profile, print
the two numbered jobs, and return three loose parts. Jake owns the M3 screws,
installation, and subsequent gripper/contact recalibration.

## Verification

- Pinned source hashes, license, and upstream 3MF material assignment pass.
- Three source shells and both fallback STLs are finite, nondegenerate,
  watertight, two-incidence manifold, and consistently outward-wound.
- 3MF OPC/XML, millimetre units, identities, coordinates, translation-only
  transforms, bed bounds, 15.0 mm PLA spacing, and CRC gates pass.
- Two plate renders and the three-component overview were visually inspected.
- Three release regression tests and 21 focused state/documentation tests pass.
- ZIP exact-content, embedded-manifest, SHA-256, and reopen gates pass.
- ZIP: `release/SO101_R1_AD5X_Compliant_Gripper_Print_Package.zip`
- Size: 6,144,138 bytes
- SHA-256: `a67d4a47613b79cf63840d59266b6448bce381d0db2559fb0b883fd9e5c09b9a`

## Delivery receipt

Gmail sent and then re-read message `19f76782947c0aef` from
`jakekinchen@gmail.com` to `Zane.cooke17@gmail.com` with subject
`SO-101 compliant gripper — AD5X two-plate print package`.

Verified attachments:

- `SO101_R1_AD5X_Compliant_Gripper_Print_Package.zip` - 6,144,138 bytes
- `README_PRINTING.md` - 2,274 bytes

The message states that a computer-use agent prepared and sent the handoff,
lists exactly two print jobs, says the plates are already arranged, requires
100% scale and no supports, and assigns assembly/calibration to Jake.

## Residual boundary

TPU brand and Shore hardness, vendor-slicer replay on Zane's machine, printed
fit, print quality, M3 screw length, grasp performance, and updated SimLink
contact calibration remain unverified. The package and email claim none of
them. T19.2f is complete as an offline print-package delivery only.
