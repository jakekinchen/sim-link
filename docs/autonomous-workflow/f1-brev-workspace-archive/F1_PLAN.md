# F1 — π0.5 on one Brev A100-80GB

## Objective

Run one ABEJA-parity full fine-tune of the exact cached `lerobot/pi05_base`
snapshot on the exact W2-recreated R0 dataset, then evaluate fixed checkpoints
in CPU MuJoCo under chunk-50 and receding-10 action-consumption semantics.

This is simulation policy-training evidence only. It grants no hardware,
physical-motion, physical-transfer, or promotion claim.

## Frozen boundaries

- Canonical `/Users/kelly/Developer/sim-link`: read only at source commit
  `471b7582a756e618aebd37845adcaccde880741d`.
- One explicit 1×A100-80GB Brev instance, one optimizer run, no retry or
  fallback chain, no H100, no multi-GPU.
- R0 identity `bd36b7c491ba3c3e08ae3efd87febdbbb1f52f917cb258399484ba4f5311a184`.
- R0 mixture `37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df`.
- R0 statistics `02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae`.
- Base revision `7de663972b7817d2c4cf2d84c821153dfea772e9`; weights SHA-256
  `0eb11ca9587678c1d2ef8cf32807c29f8ce53a2bfdfc1aa4a4c96f16fca59b0f`.
- LeRobot `e40b58a8dfa9e7b86918c374791599d070518d11` plus patch
  `efe912e3cf75c76a3b0a01d2baec8f0856ce2e2a981f4845978f0e9e34155284`.
- Training: full model, batch 8, bf16, gradient checkpointing, compile,
  5,000 steps, scheduler decay 5,000, seed 20260717.
- Checkpoints/evaluations: steps 1,000, 2,000, 3,000, 4,000, and 5,000;
  fixed simulation seed 0; chunk-50 first, receding-10 second.

## Evidence gates

1. Fresh authenticated Brev inventory and exact A100 price/availability.
2. Completion window and projected spend remain below 09:30 CDT and $100.
3. Remote preflight re-hashes all model/data/source identities and proves the
   training/evaluation output paths absent before any model load.
4. One launch command is written and executed exactly once.
5. Every checkpoint evaluation writes a signed compact receipt; best selection
   is strict success first, then maximum lift, then later checkpoint.
6. Preserve the best `pretrained_model` outside the instance before teardown.
7. Delete the non-stoppable instance immediately after required evaluation and
   artifact preservation, then record final `brev ls --json` inventory.

## Stop conditions

- Any preflight identity mismatch.
- Output path already exists.
- No remaining completion budget.
- A second create or optimizer launch would be required.
- Spend projection reaches the $100 cap.

