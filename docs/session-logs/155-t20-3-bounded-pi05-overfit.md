# Executor Session 155 - T20.3 Bounded PI0.5 Overfit

T20.3 loaded the exact pinned PI0.5 checkpoint, preprocessor, tokenizer, and
normalization state locally on MPS under the live T20.1 simulation authority.
A fresh rank-4 LoRA adapter exposed 321,792 trainable parameters. Twenty exact
optimizer updates used source-bound starts that never crossed either train
episode boundary. Train loss changed from 100.84408569335938 to
100.08732986450195 and held-out loss from 130.006591796875 to
128.40567779541016. All observed losses and gradients were finite.

The saved adapter then controlled all 244 frames of the held-out seed-2 MuJoCo
rollout through 49 five-action-horizon replans. The exact checkpoint processor
and postprocessor surrounded canonical MuJoCo-to-LeRobot coordinate conversion.
No scripted control, grasp assist, action-range projection, hardware, network,
external compute, or Brev resource was used.

The policy formed zero strict-v2 contacts and lifted the anchor
0.00000030070669393422733 m against the 0.025 m threshold. The truthful
terminal outcome is `no_strict_grasp_contact`; semantic strict success and
policy acceptance are false. The signed artifact contains five 256 px
top/wrist keyframes and measured-versus-threshold margins for every gate.

Nine focused tests passed. The broader 81-test grasp/training/coordinate gate
passed 80 tests; the sole error is the same pre-existing committed
`test_mujoco_anchor_grasp` fixture/generator drift documented at T20.2. The
review found and corrected an adapter-binding weakness before the final run:
both adapter configuration and weight bytes are now checked against the
training summary, and the final action-sequence hash reproduced exactly across
two immutable evaluations.

T20.3 closes as verified negative falsification evidence. T20.4 is next and
must treat loss as diagnostic only until a fresh strict held-out rollout passes.
