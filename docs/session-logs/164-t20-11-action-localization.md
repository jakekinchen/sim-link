# Executor Session 164 - T20.11 Action Localization

T20.11 reran PI0.5, SmolVLA, compact ACT, and compact Diffusion Policy from the
same seed-2 reset using their immutable T20.7 checkpoints and the corrected
T20.10 release semantics. Every rollout retains 244 requested-action
comparisons, five 256 px keyframes, strict gate margins, projection accounting,
and an explicit distinction between identical-reset frame-0 error and later
closed-loop compounding drift.

All four model action hashes, keyframes, and strict counts match T20.7 exactly.
Each first diverges at frame 0. PI0.5 has 0.03097 rad non-gripper MAE but
0.75432 rad gripper error. SmolVLA has 0.25102 rad non-gripper MAE and 1.77453
rad gripper error. ACT's largest initial error is 1.72632 rad wrist roll;
Diffusion's is 2.52320 rad elbow flex and it still projects 52 frames. None
makes strict contact.

The signed gate selects a PI0.5 gripper-channel semantics/weighting audit as
the narrow next hypothesis, not as model promotion. Gate identity is
`dcbf6c58...`, file hash is `72617edf...`, and 83 relevant tests pass. The
Diffusion rerun reused the existing local cached Diffusers 0.35.2 package after
the default interpreter path did not expose it; no package was installed and
no network was used. No optimizer, hardware, external compute, or Brev ran.
