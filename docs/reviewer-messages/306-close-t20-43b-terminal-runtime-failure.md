# Reviewer Decision 306 - Close T20.43b Terminal Runtime Failure

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_43B_VERIFIED_TERMINAL_RUNTIME_FAILURE_CAPABILITY_UNRESOLVED`

The sole epoch-2 T20.43b replacement attempt is consumed and closed. This is a
verified infrastructure result, not a trained-ACT negative and not a Gate C
evaluation.

## Exact terminal boundary

- Attempt started at `2026-07-16T21:32:02-05:00` from accepted origin commit
  `a6b2c94d6cceaebf5148dc934b90492bdb03e51d`.
- Marker identity `d67cf38e7d7a441da93c3af55cdcfeefe64b55ce9cf3f0b95894299a88fdca09`
  consumed permit `81b38484...`; marker file SHA is `f816fbac...`.
- A fresh ACT model and optimizer were constructed. Checkpoint 0 was saved;
  model SHA is `acc865fb...` and checkpoint identity is `916200d0...`.
- One untrained chunk-50 rollout completed with trace identity `b707b815...`
  and file SHA `0c01265d...`. It had zero strict-contact frames and
  `3.042251932594553e-7` m maximum lift, so strict-v2 was false. These are
  checkpoint-0 diagnostics, not learned-policy evidence.
- Before the required mirror could be emitted, the renderer rejected schema
  `scenesmith.t20_43b_r1_act_closed_loop_trace.v1`. The runner signed terminal
  receipt `89b6dbff17f5da345b1c8d8fa9951989eda092998b702737dd7da16c42db2e92`
  (file SHA `429431d6...`) at stage `checkpoint_0_evaluation`.
- Optimizer updates: 0. Completed checkpoints: 1. Completed rollouts: 1.
  Gate C passed: false. Retry and second replacement: false.

## Root cause

`scripts/robot_lab/render_rollout_mirror.py` dispatches T20.43 and T20.44 trace
schemas but has no T20.43b dispatch. The pre-run renderer smoke replayed the
retained original-T20.43 trace `6133ce58...`; it proved the stable interpreter
and MuJoCo support path but did not exercise the new T20.43b trace schema.
This is a deterministic evidence-path integration omission, not an ACT
training result.

## Independent verification and adversarial review

The closeout adds a model-free terminal branch to `verify_all_outputs` that
requires:

- no coexisting full run/result/scorecard/retention artifacts;
- exact signed terminal receipt reconstruction;
- exact attempt-marker identity binding; and
- byte-exact partial run-tree reconstruction.

Six focused runner tests and 35 T20.43/T20.43b/T20.44 regressions pass, as do
offline Ruff lint/format, compilation, JSON, and whitespace checks. The live
`--verify` path returns the exact terminal receipt with exit code 0. Review
found no stale-permit reuse, aliasing, non-finite value, double counting,
evidence spoofing, physical/network/external/Brev authority, or coexisting
success claim.

## Disposition

T20.43b is verified closed at a terminal runtime failure. The ACT-on-129-
episodes scientific question remains unresolved because no optimizer update
occurred. No patch-and-resume, retry, continuation, second replacement,
T20.45 activation, recipe/schedule/threshold change, hardware, network,
external compute, Brev, transfer, promotion, or destructive action is
authorized. Any future ACT attempt requires a new explicit owner decision and
a separately reviewed fail-closed authority boundary.
