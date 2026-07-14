# Slice Brief 148 - T20.17 Bounded Clean-Base Campaign

**Date:** 2026-07-14

## Objective

Run the reviewed clean `lerobot/pi05_base` campaign through the pinned official
LeRobot training entrypoint, preserve its checkpoint and loss evidence, then
evaluate the resulting policy unassisted on frozen source seed 6.

## Contract

- Reverify Brief 147's persistent dataset, training specification, complete
  local base snapshot, and live T20.17 central authority before model load.
- Invoke pinned `lerobot.scripts.lerobot_train` locally and offline with the
  exact package dataset root, exact local snapshot root, MPS, rank-4 LoRA,
  batch size 1, seed 20260714, 250 optimizer updates, zero environment
  evaluation during training, no image augmentation, no Hub push, and no
  external logger.
- Use LeRobot's package dataset metadata statistics at processor construction.
  Do not install a SceneSmith normalizer, change the split, resume a checkpoint,
  fabricate a camera, pad state/actions, or fetch another model.
- Write to a new immutable run root. Bind the resolved configuration, package
  training log, final checkpoint, adapter bytes, processor files, and finite
  loss trace. Fail closed on a missing update, non-finite metric, base mismatch,
  or output overwrite.
- Evaluate only the final candidate through the existing policy-owned
  unassisted MuJoCo adapter on held-out seed 6. Record every projection,
  assistance, contact, lift, and strict-v2 gate. A failure is a verified
  negative result, never a promotion.
- Do not access hardware or cameras, start external compute or Brev, push a
  model to a Hub, or grant physical transfer, promotion, or policy acceptance.

## Acceptance Criteria

- The official LeRobot entrypoint completes exactly 250 finite local-MPS
  optimizer updates from the bound clean base with rank-4 PEFT.
- The saved checkpoint and processor evidence mechanically bind to Brief 147's
  source dataset, package statistics, model revision, and campaign identity.
- Frozen seed-6 evaluation runs without scripted/controller assistance. Its
  strict result, positive or negative, is signed and reproducible.
- Focused tests, relevant regressions, same-agent adversarial review, state,
  ledger, plan, session log, reviewer decision, scoped commit, and remote branch
  agree before T20.17 is described as verified.

## Out Of Scope

Hardware/camera access; physical transfer; promotion; Brev; external compute;
Hub publishing; alternate checkpoints; extra updates; recovery data; domain
randomization; T20.18-T20.22; policy acceptance without repeatable strict-v2
success.
