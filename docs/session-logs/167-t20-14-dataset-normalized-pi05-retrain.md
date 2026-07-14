# Executor Session 167 - T20.14 Dataset-Normalized PI0.5 Retrain

T20.14 completed the exact T20.7 ordered 20-sample schedule with rank-4 PI0.5
LoRA on local MPS. The only intervention was the frozen T20.13 train-only
state/action normalizer; all six loss weights remained 1.0. No external or Brev
compute ran.

Mean train loss changed from 6.17389 to 6.16356 and held-out loss from 3.35973
to 3.35389. The fixed seed-2 corrected closed loop used 244 policy-owned frames
with zero projection and zero assistance. It produced zero strict-v2 frames in
every phase, only 3.007e-7 m maximum lift against the 0.025 m gate (margin
-0.0249997 m), and terminal outcome `no_strict_grasp_contact`.

Relative to the T20.11 checkpoint-normalized PI0.5 baseline, initial gripper
error improved from 0.75432 to 0.23898 rad. Initial non-gripper MAE regressed
from 0.03097 to 0.74683 rad, a 24.114x increase, with wrist roll dominant at
1.34876 rad. This mixed effect rejects a capability claim and does not justify
more optimizer updates.

Five 256 px pregrasp/close/hold/lift/retreat keyframes were reviewed in top and
wrist views. The gripper remains visibly displaced from the cube throughout;
no contact or lift is visible. The signed evaluation identity is `e8f381a2...`,
file hash `5ac49777...`, checkpoint hash `ed7c06a6...`, and 40 focused tests
pass.
