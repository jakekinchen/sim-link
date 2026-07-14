# Executor Session 169 - T20.16 Hybrid Gripper Postprocessor Rollout

T20.16 deep-copied the pinned checkpoint processor, retained checkpoint state
preprocessing and action statistics for joints 0-4, and replaced only gripper
action mean/std with the T20.13 train-only dataset statistics. It performed no
optimizer step or checkpoint mutation.

The deterministic frame-zero preflight matched the T20.15 prediction: arm MAE
was 0.0308807 rad and gripper error was 0.1201542 rad, both within 1e-6 rad.
The fixed seed-2 corrected strict rollout then used 244 policy-owned frames.
Trajectory MAE rose to 0.906029 rad, every strict-v2 phase count remained zero,
and maximum lift was 3.007e-7 m against the 0.025 m gate. Terminal outcome was
`no_strict_grasp_contact`.

All 245 policy calls round-tripped through the bounded coordinate conversion
without clipping above 1e-6, and the simulator projected zero action frames.
Five 256 px stages were reviewed in top and wrist views: the arm and gripper
remain below-left of the cube and the wrist view loses the object. No contact
or lift is visible.

The signed gate identity is `d0c1bd1...`, file hash `22326791...`; the source
rollout identity is `1a15279d...`, file hash `7f146f86...`. Thirty-nine focused
tests pass. The hybrid is retired. The sole next hypothesis is clean
`pi05_base` initialization with dataset statistics in both directions and a
realistic supervision/update budget. No hardware, external compute, or Brev
was used.
