# Slice Brief 166 - T20.35 Gate B Rank-Capacity Discriminator

**Date:** 2026-07-14

**State:** `in_progress`

## Objective

Test the single capacity hypothesis routed by T20.34: whether increasing only
PI0.5 LoRA rank from 4 to 16 is sufficient for the exact T20.33 one-batch Gate
B proof under the unchanged update budget and pass thresholds.

## Contract

- Reuse byte-for-byte the T20.33 source batch, dataset statistics, base model,
  task, processor/postprocessor path, horizon, learning rate, 500 updates,
  training seed, five inference seeds, objective-ratio gate, and 0.05 rad
  all-chunk action gate. Change only LoRA rank and alpha from 4 to 16.
- Produce a new signed specification, owner-scope grant, central-composer
  request, and `simulation_training_ready` decision. Tests, same-agent pre-run
  review, state, commit, push, and remote confirmation must agree before model
  load or optimizer creation.
- Run exactly once from the clean pinned base. Record every finite objective
  and gradient, checkpoint tree, and five full decoded chunks. No retry,
  continuation, second rank, second batch, or hyperparameter change.
- Gate B passes only under the unchanged T20.33 criteria: every decoded chunk
  maximum error <= 0.05 rad and final five-seed objective <= 10% of baseline.
  A failure remains a verified negative and blocks Gate C/broader campaigns.
- No closed-loop rollout, dataset/statistics/twin change, hardware, camera,
  external compute, Brev, policy acceptance, transfer, or promotion.

## Acceptance Criteria

- Deterministic tests reject any drift beyond rank/alpha, plus source, update,
  seed, threshold, non-finite, result, and authority mutation.
- Pre-run implementation and central training-only authority are reviewed and
  remotely preserved before the one optimizer run.
- One signed result makes exactly one pass/fail decision and compares rank-16
  evidence with the frozen rank-4 boundary without relabelling either.
- Focused/broad tests, adversarial review, state, ledger, plan, session log,
  reviewer decisions, scoped commits, and remote preservation agree.

## Out Of Scope

Any rank other than 16; rank sweep; extra updates; continuation; second batch;
Gate C work; full campaign; closed-loop rollout; promotion; hardware; external
compute; Brev; or global authority change.
