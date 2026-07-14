# Session Log 188 - T20.24 Recovery-Augmented Local-MPS Campaign

## Scope

Brief 155 executed the exact centrally authorized T20.23 local campaign and
evaluated the frozen result on held-out seeds 6 and 7. No hardware, camera,
physical robot, external compute, or Brev was used.

## Runtime Boundary

Run 001 failed before optimizer step 1 because `uv` selected Python 3.14 and
the pinned argument parser rejected a `str | None` type. The failed invocation
and log remain preserved. Python 3.11 was then rejected by LeRobot's declared
`>=3.12` requirement before code launch. Run 002 used an isolated Python 3.12
environment, started cleanly, and did not resume any failed state.

## Training Evidence

- Dataset: 10 episodes / 2,330 frames, exact T20.23 identity.
- Device and adapter: local MPS, rank-4 LoRA, 321,792 trainable parameters.
- Optimizer updates: exactly 500; every logged loss finite.
- Loss: 1.483 baseline, 0.603 final, 0.018 minimum.
- Run-summary identity:
  `8b54bba54305f635a911494f4f68695974d0958ff613ea6f46243c0f66f2f47c`.
- Checkpoint-tree identity:
  `045460f69d8402eabb784731731295fbb64906203787bd6f6bb4ffe58675b330`.
- Adapter SHA-256:
  `9bc549ee3f7b92bc8a50216645fae45398d228c236637bbc593b30debb2cb0b4`.

## Frozen Evaluation

- Seed 6 identity:
  `21f8fd46ee2b174dfed1503326f82f5c2162665241683ccc54458f7fc7ae30a5`;
  zero strict contact, 0.000144 mm maximum lift, no projection/assistance.
- Seed 7 identity:
  `7a8a5b14dd16356d1dc2949fc74dce21bb55aa89654f0c3a9f589884fa4f9b3b`;
  zero strict contact, 0.000143 mm maximum lift, no projection/assistance.
- Result-gate identity:
  `480f812ce360e16784a9c087cf6500c94c9cc0363ca591e9e648c0b74097411b`.
- Decision: `candidate_failed_two_seed_strict_v2`; strict success 0/2.

## Validation And Review

Forty-seven relevant tests passed across T20.17-T20.24 campaign/data/recovery,
central authority, artifact contracts, and coordinates. The run summary and both
evaluation payloads reverified as signed evidence. The aggregate result was
recomposed from live files and matched exactly.

Same-agent adversarial review covered partial-run preservation, update and loss
accounting, checkpoint tree and base binding, dataset/spec/authority identities,
two-seed uniqueness and source binding, finite outputs, strict-v2 truth, no
projection/assistance, signed mutation, authority escalation, and cleanup.

## Result

This is a verified negative learned-policy result. Recovery-augmented training
did not produce contact on either held-out seed. No accepted-policy pointer
changes, and no transfer, promotion, hardware, external-compute, or Brev
authority is created. The next safe causal step is offline policy/output
localization before any further optimizer budget.
