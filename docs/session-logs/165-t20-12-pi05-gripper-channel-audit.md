# Executor Session 165 - T20.12 PI0.5 Gripper-Channel Audit

T20.12 traced all 488 train and 244 held-out actions from MuJoCo radians
through the canonical LeRobot degree/percent conversion, the pinned PI0.5
mean/std normalizer, and the inverse postprocessor. The maximum inverse
round-trip error is 3.606e-9 rad against a 1e-8 rad limit. The frame-zero
source-to-float32 tensor difference is 2.384e-8 rad against a 1e-7 rad limit,
and the reconstructed T20.11 gripper error agrees within that same tolerance.

The gripper is not underweighted: all six action dimensions have weight 1.0
and equal one-sixth aggregation share. Instead, the frozen checkpoint
normalizer is broadly out of domain for this geometry-derived dataset.
Shoulder lift, wrist flex, wrist roll, and gripper exceed its observed min/max;
the open gripper is 92.4302% versus checkpoint max 81.0264% (margin -11.4037
percentage points) and q99 60.0100% (margin -32.4202). Wrist-roll normalized
target mean-square is 412.39 in train, so gripper-only reweighting is not the
supported next intervention.

The signed artifact identity is `12aacb3c...`, file hash is `e6c706da...`, and
47 relevant tests pass. No optimizer, checkpoint or dataset mutation,
hardware, external compute, or Brev ran.
