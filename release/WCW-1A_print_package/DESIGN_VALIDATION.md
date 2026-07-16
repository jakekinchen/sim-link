# WCW-1A design validation

Generated from tracked parametric source and independently parsed from every final binary STL. All dimensions are millimetres. PLA estimates use 1.24 g/cm3 and 100% solid printing; weigh-back remains the as-built truth.

## STL results

| File | Bounds mm | Vertices | Faces | Volume mm3 | PLA g | Mesh |
|---|---|---|---|---|---|---|
| WCW-1A_R1_C0_ball-retainer_exterior-face-down.stl | 1.60 x 49.90 x 24.00 | 825 | 1650 | 1890.4 | 2.34 | PASS |
| WCW-1A_R1_C0_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 153 | 302 | 42133.5 | 52.25 | PASS |
| WCW-1A_R1_C1_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 1174 | 2356 | 1961.1 | 2.43 | PASS |
| WCW-1A_R1_C1_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 350 | 696 | 34932.0 | 43.32 | PASS |
| WCW-1A_R1_C2_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 1306 | 2624 | 1956.1 | 2.43 | PASS |
| WCW-1A_R1_C2_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 353 | 702 | 34932.3 | 43.32 | PASS |
| WCW-1A_R1_C3_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 1653 | 3326 | 2026.8 | 2.51 | PASS |
| WCW-1A_R1_C3_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 542 | 1080 | 27730.5 | 34.39 | PASS |
| WCW-1A_R1_C4_ball-retainer_exterior-face-down.stl | 5.90 x 49.90 x 24.00 | 1788 | 3600 | 2021.8 | 2.51 | PASS |
| WCW-1A_R1_C4_carrier_print-minus-x-face-down.stl | 33.50 x 54.40 x 25.00 | 553 | 1102 | 27731.1 | 34.39 | PASS |
| WCW-1A_R1_ball-fit-coupon_20p4-20p6-20p8mm.stl | 90.00 x 38.00 x 4.00 | 2666 | 5340 | 9303.6 | 11.54 | PASS |
| WCW-1A_R1_body_top-down.stl | 40.00 x 60.00 x 65.00 | 91 | 178 | 34144.0 | 42.34 | PASS |
| WCW-1A_R1_bottom-lid_outer-face-down.stl | 39.40 x 59.40 x 6.10 | 240 | 476 | 10482.5 | 13.00 | PASS |

All 13 meshes open as binary STL, have zero boundary/non-manifold edges, zero duplicate or degenerate faces, consistent stored normals, positive signed volume, and matching Blender source validation.

## Assembled mass and center of mass

| Config | Balls | Est. mass g | CoM x,y,z mm | Shift from C0 mm |
|---|---|---|---|---|
| C0 | 0 | 109.93 | (-0.329, -0.020, -8.722) | (0.000, 0.000, 0.000) |
| C1 | 1 | 133.80 | (-0.481, -0.015, -9.699) | (-0.152, 0.005, -0.976) |
| C2 | 1 | 133.79 | (-0.482, 2.663, -9.699) | (-0.153, 2.683, -0.976) |
| C3 | 2 | 157.66 | (-0.588, -0.011, -10.380) | (-0.259, 0.009, -1.657) |
| C4 | 2 | 157.66 | (-0.588, -0.010, -10.380) | (-0.259, 0.009, -1.658) |

C1/C2 ball count is equal; estimated printed mass mismatch from tactile ID geometry and tessellation is 0.0058 g, below ordinary FDM/scale repeatability. C2 produces the intended +y CoM shift. C3/C4 remain centered in y to practical precision while the ball y-squared sum increases from 242 to 450 mm2.

## Audit disposition

1. Units/scale: source and manifests freeze millimetres; body is 40 x 60 x 65 mm.
2. Balls: nominal diameter and diametral fit allowance are separate parameters; expected 19.8-20.2 mm balls use a 20.8 mm bore.
3. Pocket clearance: 0.8 mm nominal / 0.6 mm at a 20.2 mm ball, verified by a 20.4/20.6/20.8 coupon.
4. Insertion: every well is open after printing; the ball enters from +x.
5. Retention/rattle: 45-degree cone plus 0.20 mm spring-boss preload; hand-shake QC is mandatory.
6. No trapped print: body, lid, carriers, and retainers are separate; no enclosed support exists.
7. Fits: 0.35 mm/side lid plug clearance, at least 0.4 mm cartridge/body clearance, 0.20 mm retainer slide clearance.
8. Keying: one -x/+y rail and matching notches prevent 180-degree cartridge/lid insertion.
9. Material: body wall 2.4, roof 2.8, pocket outer walls 1.8/2.1, local C3 inter-pocket web 1.2 mm.
10. Grasp faces: central 18 mm bands are uninterrupted flat body surfaces.
11. Corners: 2.0 mm body chamfers and smaller part chamfers remove gripper-damaging edges.
12. Printability: top-down body; vertical conical wells; 0.8 mm rail lips; no support material required.
13. Retention hardware: printed detents/springs only; no screws, magnets, or inserts.
14. Tag planes: flat exterior PLA; unique tag36h11 IDs 0-4; one-module white border.
15. Occlusion: x-face labels occupy z=11.5-31.5 mm, above the z=-9 to +9 mm grasp band.
16. Mesh integrity: all automated manifold, edge, normal, duplicate, degeneracy, and volume gates pass.
17. Interference: analytic assembly fit checks report no unintended overlap; only ball preload, lid detents, retainer detent, and crush ribs intentionally interfere.
18. CoM conditions: C2 shifts +y relative to C1; C3/C4 remain centered while C4 increases ball-distribution inertia.

## Residual physical risk

No software-only workflow can prove a specific printer's hole bias, layer adhesion, spring fatigue, label adhesive, or the exact Amazon ball tolerance. The coupon-first sequence, 0.8 mm diametral pocket allowance, compliant preload, and QC shake test reduce those risks. Actual ball and finished-part masses should be measured before treating the numeric mass/CoM estimates as metrology truth.
