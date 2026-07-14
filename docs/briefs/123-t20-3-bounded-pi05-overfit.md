# Slice Brief 123 - T20.3 Bounded PI0.5 Overfit

**Date:** 2026-07-14

## Objective

Repeat T20.2's tiny-overfit falsification with the pinned local PI0.5
checkpoint. Establish whether a bounded optimizer run over the two T20.1 train
episodes changes loss and held-out closed-loop grasp behavior.

## Contract

- Revalidate the live T20.1 central authority immediately before checkpoint
  load and optimizer execution. Use local MPS only; network, hardware, external
  compute, and Brev are forbidden.
- Bind the exact T20.1 specification and tensor-view hashes. Train only on
  seeds 0 and 1; seed 2 remains held out.
- Convert the six MuJoCo-radian position/action values into canonical LeRobot
  body degrees and gripper percent before the pinned checkpoint preprocessor.
  Do not infer velocity support or feed evaluator-only fields.
- Use the exact cached `Cache-SCA/pi05_teleop_sort_block` checkpoint,
  preprocessor, tokenizer, normalization statistics, prompt semantics, and
  pinned patched LeRobot runtime. Missing or changed bytes fail closed.
- Keep the run bounded and immutable. Record trainable parameter scope, exact
  update count, realized sample starts, finite losses/gradients, source hashes,
  and checkpoint hash. A training loss change is not semantic task success.
- Evaluate the saved model separately in the held-out seed-2 MuJoCo scene with
  policy-owned controls. Record terminal outcome, strict-v2 gate margins,
  assist/projection counts, and three to five 256 px keyframes.

## Acceptance Criteria

- A deterministic local run either completes with finite evidence or preserves
  an exact, truthful resource/runtime failure without weakening the contract.
- A fresh held-out closed-loop rollout distinguishes policy behavior, terminal
  outcome, strict semantic success, and policy acceptance. No physical,
  transfer, promotion, or deployment claim is permitted.

## Out Of Scope

T20.4 update ladders, model bake-offs, physical hardware, external compute,
Brev, checkpoint promotion, and destructive cleanup.

## Verified Outcome

Implementation boundaries `657258e46a39e8a7cabe1068db5ac7b64e07cb02`
and `7ffd48e721c5ba28bc1283481df86f542076a897` completed the bounded
source-bound run and strict held-out evaluator. Twenty local MPS LoRA updates
used 321,792 trainable parameters and changed train loss from
100.84408569335938 to 100.08732986450195 and held-out loss from
130.006591796875 to 128.40567779541016. All losses and gradients were finite.

The deterministic 244-frame seed-2 rollout used 49 policy replans, zero action
projections, and zero assist frames. It made zero strict-v2 contacts and lifted
the anchor 0.00000030070669393422733 m against the 0.025 m threshold. Five
256 px top/wrist keyframes and measured-versus-threshold gate margins are bound
in the signed artifact. The result is a verified negative and is not promoted.
