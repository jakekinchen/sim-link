# WCW-1A printing instructions

This package is ready to slice in millimetres. Print every STL as a separate part; do not arrange an assembled cube in the slicer.

## Primary material and settings

- Material: matte PLA or PLA+, preferably matte white or light gray for the body. Neutral filament already on hand is fine for the internal cartridges and lid. PETG is an acceptable fallback, but expect slightly looser spring/detent behavior.
- Nozzle: 0.4 mm. Layer height: 0.20 mm (0.16 mm is acceptable for the retainers).
- Perimeters: 4. Top/bottom solid layers: 6. Infill: 100% rectilinear/lines for repeatable mass properties.
- Supports: none. The ball wells use 45-degree conical seats and vertical bores. Rail lips overhang only 0.8 mm.
- Brim: 5 mm on the tall body; optional 2-3 mm on carriers if the filament tends to warp. No brim normally needed on lid, retainers, or coupon.
- Elephant-foot compensation: 0.15 mm if available. Do not uniformly scale any part.
- Use a smooth, clean build plate for the body top face because the top AprilTag label mounts there.

## Print the coupon first

Print `WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl`. After cooling, every ball intended for the kit must pass freely through the labeled 20.8 mm ring. The 20.4 and 20.6 mm rings show the printer's actual hole bias. If 20.8 mm does not pass, use the slicer's hole-size compensation to recover the measured 20.8 mm opening (typically about +0.10 mm, never more than +0.20 mm without rechecking), reprint the coupon, and do not scale the whole model.

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

Recommended order: coupon; one C1 carrier and C1 retainer for fit confirmation; remaining carriers/retainers; lid; body last.

The AprilTag PDF/PNGs are labels. Do not print them as plastic geometry. Print the PDF at Actual Size / 100%, verify the 100.0 mm line, cut on the gray border, and apply after dimensional QC.
