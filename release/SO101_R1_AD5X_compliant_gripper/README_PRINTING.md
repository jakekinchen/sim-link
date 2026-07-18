# SO-101 compliant gripper - FlashForge AD5X print handoff

There are exactly **two print jobs**. Open the two numbered 3MF files in order.
The objects are already split by material, oriented, centered, and arranged for
the AD5X 220 x 220 mm bed. Do not split, rotate, scale, or auto-arrange them.

## Job 1 - rigid bases

- File: `plates/SO101_R1_AD5X_plate01_PLA_gripper-bases.3mf`
- Material: ordinary PLA or PLA+; any color
- Copies: one plate, containing both required base pieces
- AD5X/default nozzle: 0.4 mm
- Layer height: 0.20 mm
- Walls: 2 (the upstream XLeRobot project setting)
- Top/bottom: 5 top, 3 bottom
- Infill: 15% grid
- Supports: off
- Scale: 100%
- Approximate solid-model mass before slicer infill: 66.0 g

## Job 2 - soft finger

- File: `plates/SO101_R1_AD5X_plate02_TPU95A_soft-fin.3mf`
- Material: TPU around Shore 95A. If the spool is substantially softer or
  harder, pause and tell Jake before printing.
- Copies: one plate, containing the complete Fin-Ray finger
- AD5X/default nozzle: 0.4 mm
- Layer height: 0.20 mm
- Walls: 2
- Infill: 15% grid
- Supports: off; the upstream design explicitly avoids TPU supports
- Scale: 100%
- Use the spool manufacturer's temperature plus your tuned AD5X TPU flow,
  speed, and retraction settings. Those are intentionally not embedded.
- Feed TPU through the shortest straight external path; do not route TPU
  through IFS. FlashForge lists TPU 95A as AD5X-compatible but not IFS-compatible.
- A 3 mm brim is optional only if first-layer adhesion is marginal.
- Approximate solid-model mass before slicer infill: 12.4 g

## What to send back

Please return the three printed pieces loose. Jake will provide the two M3
screws and perform installation/calibration. No assembly work is needed from
the printer.

## Fallback

If a 3MF does not open correctly, import the correspondingly named file in
`fallback_stl/`. Each fallback STL is already arranged as the same complete
material plate.

## Important calibration note

This compliant gripper changes the robot's contact surfaces and compliance.
It must be measured and added to SimLink before any calibrated real-to-simulation
or grasp result is claimed. Printing the parts does not itself verify physical
fit, grip performance, or robot calibration.
