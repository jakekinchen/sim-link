# WCW-1A printing instructions

This replacement package is ready to slice in millimetres. Prefer the arranged 3MF plate files below; the individual STLs remain available as a fallback or for reprinting one damaged part. Never import the assembled render as geometry.

## Bambu Studio batched print paths

The 3MF files contain independent, named objects already rotated into the documented support-free orientations and arranged at z=0. They are standard 3MF files, not a printer-specific sliced job: in Bambu Studio, select the actual printer/nozzle/plate and the settings below, confirm every object remains on the bed, and slice. Do not use auto-arrange unless you intentionally want to replace the verified spacing.

**Preferred 256 x 256 mm path (typical Bambu A1, P1, and X1 class): two print jobs total.**

1. Print `plates/WCW-1A_R1_Bambu_plate00_fit-coupon_fits180mm.3mf`. Let it cool and verify all six selected balls pass the 20.8 mm ring.
2. If the coupon passes, print `plates/WCW-1A_R1_Bambu_256mm_plate01_full-production-kit.3mf`. It contains all 12 production parts exactly once: body, lid, five carriers, and five retainers.

**180 x 180 mm fallback (Bambu A1 mini or another small bed): four print jobs total.**

1. Universal fit coupon above.
2. `plates/WCW-1A_R1_Bambu_180mm_plate01_C1-fit-check.3mf` - C1 carrier and retainer.
3. After the C1 pair slides and detents correctly, `plates/WCW-1A_R1_Bambu_180mm_plate02_remaining-hardware.3mf` - the other eight cartridge parts plus lid.
4. `plates/WCW-1A_R1_Bambu_180mm_plate03_body.3mf` - body alone for the safest tall-part adhesion.

| 3MF plate | Declared bed mm | Objects | Route |
|---|---|---|---|
| WCW-1A_R1_Bambu_plate00_fit-coupon_fits180mm.3mf | 180 x 180 | 1 | universal_preflight |
| WCW-1A_R1_Bambu_256mm_plate01_full-production-kit.3mf | 256 x 256 | 12 | primary_256mm |
| WCW-1A_R1_Bambu_180mm_plate01_C1-fit-check.3mf | 180 x 180 | 2 | fallback_180mm |
| WCW-1A_R1_Bambu_180mm_plate02_remaining-hardware.3mf | 180 x 180 | 9 | fallback_180mm |
| WCW-1A_R1_Bambu_180mm_plate03_body.3mf | 180 x 180 | 1 | fallback_180mm |

Use one filament for a no-intervention batch. If an AMS is available, Zane may assign white/light gray to the body and neutral colors to internal objects, but color assignment is optional and is not embedded in these neutral standard 3MFs.

## Primary material and settings

- Material: matte PLA or PLA+, preferably matte white or light gray for the body. Neutral filament already on hand is fine for the internal cartridges and lid. PETG is an acceptable fallback, but expect slightly looser spring/detent behavior.
- Nozzle: 0.4 mm. Layer height: 0.20 mm (0.16 mm is acceptable for the retainers).
- Perimeters: 4. Top/bottom solid layers: 6. Infill: 100% rectilinear/lines for repeatable mass properties.
- Supports: none. The ball wells use 45-degree conical seats and vertical bores. Rail lips overhang only 0.8 mm.
- Brim: 5 mm on the tall body; optional 2-3 mm on carriers if the filament tends to warp. No brim normally needed on lid, retainers, or coupon.
- Elephant-foot compensation: 0.15 mm if available. Do not uniformly scale any part.
- Use a smooth, clean build plate for the body top face because the top AprilTag label mounts there.

## Print the coupon first

Use `plates/WCW-1A_R1_Bambu_plate00_fit-coupon_fits180mm.3mf`; the equivalent individual fallback is `stl/WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl`. After cooling, every ball intended for the kit must pass freely through the labeled 20.8 mm ring. The 20.4 and 20.6 mm rings show the printer's actual hole bias. If 20.8 mm does not pass, use the slicer's hole-size compensation to recover the measured 20.8 mm opening (typically about +0.10 mm, never more than +0.20 mm without rechecking), reprint the coupon, and do not scale the whole model.

## Copy count and orientation

| STL | Bounding size mm | Solid PLA estimate g | Copies |
|---|---|---|---|
| WCW-1A_R1_C0_ball-retainer_exterior-face-down.stl | 1.60 x 49.90 x 24.00 | 2.34 | 1 |
| WCW-1A_R1_C0_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 52.25 | 1 |
| WCW-1A_R1_C1_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 2.43 | 1 |
| WCW-1A_R1_C1_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 43.32 | 1 |
| WCW-1A_R1_C2_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 2.43 | 1 |
| WCW-1A_R1_C2_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 43.32 | 1 |
| WCW-1A_R1_C3_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 2.51 | 1 |
| WCW-1A_R1_C3_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 34.39 | 1 |
| WCW-1A_R1_C4_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 2.51 | 1 |
| WCW-1A_R1_C4_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 34.39 | 1 |
| WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl | 90.00 x 38.00 x 4.00 | 11.54 | 1 |
| WCW-1A_R1_body_top-down.stl | 40.00 x 60.00 x 65.00 | 42.34 | 1 |
| WCW-1A_R1_bottom-lid_outer-face-down.stl | 39.40 x 59.40 x 6.10 | 13.00 | 1 |

- Body: top/+z tag face on the bed, open bottom upward. This is intentionally top-down.
- Bottom lid: large flat outer face on the bed; keyed plug and crush ribs upward.
- C0-C4 carriers: closed -x face on the bed; open ball wells and retainer rails upward.
- C0-C4 retainers: flat exterior face on the bed; spring bosses upward.
- Coupon: broad flat face on the bed, engraved labels upward.

Recommended order is the two-job 256 mm path when the selected Bambu profile shows a 256 x 256 mm bed; otherwise use the four-job 180 mm fallback. The individual-STL order remains coupon; C1 carrier/retainer; remaining hardware; body.

The AprilTag PDF/PNGs are labels. Do not print them as plastic geometry. Print the PDF at Actual Size / 100%, verify the 100.0 mm line, cut on the gray border, and apply after dimensional QC.
