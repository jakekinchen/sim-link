# Executor Session 154 - T20.2 Bounded ACT Overfit

T20.2 ran a source-bound LeRobot ACT model locally on MPS under the live T20.1
simulation-only authority. An immutable 100-update run reduced train L1 from
1.0217032432556152 to 0.16815676142772037 and measured held-out L1
0.22133693750947714. All observed losses and gradients were finite, but the
result did not meet the near-zero-overfit hypothesis.

The saved checkpoint then controlled all 244 frames of a fresh held-out seed-2
MuJoCo rollout from reset through the declared episode horizon. No scripted
control, grasp assist, or action-range projection was used. The policy formed
zero strict-v2 grasp contacts and lifted the anchor 0.0002023007066939697 m
against the 0.025 m threshold, so the truthful terminal outcome is
`no_strict_grasp_contact` and strict semantic success is false. The signed
artifact includes five 256 px top/wrist keyframes and measured gate margins.

Focused evaluator/evidence tests passed. A targeted 87-test robotics gate
passed 86 tests; the sole failure is the pre-existing committed
`test_mujoco_anchor_grasp` fixture/generator drift and is independent of this
slice. A repository-wide discovery run is not a configured gate in this
runtime: it passed 597 of 675 tests and failed on missing optional SceneSmith
dependencies plus hardware-fixture tests that correctly reject the now-open
training lock. No hardware, external compute, or Brev resource was used.

T20.2 closes as a verified negative falsification result. It does not promote
the checkpoint. T20.3 is next, but must start in a new major-slice window
because the current no-new-slice cutoff has passed.
