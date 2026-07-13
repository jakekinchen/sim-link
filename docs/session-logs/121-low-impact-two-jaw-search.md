# Session 121 - Low-Impact Two-Jaw Search

**Date:** 2026-07-13

Brief 091 executed a fixed 20-candidate grid across five wrist-roll values and
four object-relative pregrasp heights. The nominal object, pinned MJCF, seed,
initial pose, close target, interpolation, and contact semantics stayed fixed.
Each accepted contact requires `gripper` and `moving_jaw_so101_v1` in the same
MuJoCo frame; contacts accumulated across time do not count.

The selected candidate is wrist roll -1.5 rad at 0.018 m height. Peak contact
force is 4.1971684 N, below the 5 N gate. It produces 11 simultaneous two-jaw
frames while closing and all 8 during the pre-lift hold. Contact occurs over
0.2395 to 16.724525 normalized gripper percent; metric fingertip separation
remains unknown.

The selected unassisted lift was repeated exactly. No weld or equality assist
ever activated. Two-jaw contact persists for only 4 lift frames, then the object
slips. The 12-frame lift hold contains zero two-jaw frames, and the object ends
at 0.324974 m rather than maintaining the 0.35 m clearance threshold. This is a
low-impact contact candidate, not a grasp success.

Artifact `5a5de249...` contains all candidate summaries plus 148 raw frames from
the selected lift validation. Two focused tests pass. No hardware, physical
motion, inference, optimizer, training, Brev, paid compute, or network was used.
