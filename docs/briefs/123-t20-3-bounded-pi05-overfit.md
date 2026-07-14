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
