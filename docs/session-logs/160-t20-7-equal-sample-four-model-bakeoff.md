# Executor Session 160 - T20.7 Equal-Sample Four-Model Bake-Off

T20.7 executed the reviewed exact 20-update/20-sample local-MPS rung for
PI0.5, SmolVLA, compact ACT, and compact Diffusion Policy. Every result binds
the same ordered starts, 50-action targets, source tensor and semantic
identities, runtime, initialization, optimizer settings, finite losses and
gradients, and re-hashed immutable checkpoint bytes. Absolute losses remain
model-specific diagnostics and were not used to select a winner.

All four checkpoints then ran the same held-out seed-2, inference-seed-1703,
244-frame policy-owned MuJoCo loop at action horizon 5. Every rollout records
five 256 px keyframes, the policy action-sequence hash, zero assistance, and
measured-versus-threshold margins for every strict gate. PI0.5, SmolVLA, and
Diffusion moved the anchor 0.0003007 mm; ACT moved it 2.4213 mm versus the
25 mm lift gate. All four produced zero strict contacts and zero strict
successes. Diffusion additionally requested out-of-range actions on 52 frames,
so it fails the plan's no-projection comparison contract.

The same-agent visual audit confirms ACT's gripper remains below and offset
from the object through pregrasp, close, grasp-hold, and unsupported-lift
keyframes. Its displacement is not a grasp or capability breakthrough. The
signed evaluation gate therefore records no winner and a verified negative
T20.7 outcome. No hardware, physical transfer, promotion, external compute, or
Brev was used.
