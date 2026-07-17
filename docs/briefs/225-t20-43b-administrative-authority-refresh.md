# Slice Brief 225 - T20.43b Administrative Authority Refresh

**Date:** 2026-07-16

## Objective

Implement and fixture-test the smallest epoch-2 administrative wrapper needed
to execute the already accepted T20.43b ACT replacement after its first owner
window expired before the marker. Preserve the original Gate A, renderer smoke,
dataset, ACT recipe, replacement ordinal, attempt ordinal, output paths, and
strict-v2 evaluation unchanged. Commit, push, and review the implementation
before materializing any refreshed authority.

## Owner direction and time-budget basis

- The owner now explicitly directs this thread to resolve the final unanswered
  ACT-on-129-episodes question.
- Reviewer 302 proved the original marker, model, optimizer, run, result, and
  failure paths were absent at closeout. This slice must prove those facts again
  from the current checkout before it can emit epoch-2 authority.
- The refresh remains bounded to at most eight hours. It is intended only for
  the unchanged noninterruptible 10,000-update/14-rollout campaign, whose
  closest completed standardized comparison consumed 7,506 seconds.

## Immutable inputs

- Original T20.43b spec `13c5bb4b...`, Gate A `ea65f3d1...`, renderer smoke
  `35224058...`, owner/decision/runtime/permit bundle, Reviewer 301 acceptance
  `525de8dc...`, and Reviewer 302 closeout remain immutable at their existing
  paths and identities.
- Exact R0 remains 129 episodes/31,366 frames with all held-out rows excluded.
- Recipe remains fresh ACT, seed `20260801`, batch 8, AdamW `1e-5`/`1e-4`,
  10,000 updates, checkpoints `[0,500,1000,2500,5000,7500,10000]`, and both
  chunk-50 and receding-10 strict-v2 rollouts at every checkpoint.

## Refresh contract

- Add separately named epoch-2 owner, central request/decision, runtime,
  permit, and reviewer-bound acceptance artifacts. Never rewrite epoch 1.
- The central composer must mechanically grant only
  `simulation_training_ready` for the fresh bounded interval.
- Fresh runtime evidence must prove origin preservation, exact dependencies and
  MPS/cache/support-tree facts, unchanged reviewed implementation, immutable
  epoch-1 identities, and absence/unaliased state for the sole marker and every
  run/result path.
- Epoch 2 must bind replacement ordinal 1, attempt ordinal 1, one authorized
  attempt, no retry, and the same marker/output paths. It is an administrative
  time refresh, not a second replacement or second attempt.
- The runner may consume epoch 2 only after the implementation, materialized
  authority, reviewer decision, and signed acceptance are each exact on
  `origin/codex/pi05-autolearn-loop`.

## Verification

- Add deterministic tests for time-window overflow, marker/output collision,
  base-artifact drift, central-authority escalation, attempt/replacement count
  drift, retry, and reviewer/permit mismatch.
- Run the T20.43b focused suite, T20.43/T20.44 regressions, authority-composer
  tests, strict JSON, compilation, lint/format, whitespace, and a fresh
  same-agent adversarial review.

## Authority withheld

This brief opens implementation and model-free fixture tests only. It grants no
live authority materialization, marker, backbone/model tensor read, model
construction or inference, optimizer, checkpoint, rollout, Gate C result,
retry, second replacement, recipe/schedule/threshold change, hardware, camera,
serial, physical motion, network, package installation, external compute,
Brev, transfer, promotion, or destructive operation.

## Implementation boundary

The separately named epoch-2 owner/composer/runtime/permit/acceptance contract,
exclusive materializer, reviewer-bound acceptance writer, and runner linkage
are implemented without changing the frozen T20.43b spec, Gate A, smoke,
dataset, marker, output paths, recipe, or evaluation. Four refresh tests, 34
T20.43/T20.43b/T20.44 tests, and 42 artifact/composer/pointer/receipt tests pass
with offline lint/format, compilation, CLI, JSON, and whitespace checks.
Reviewer 304 opens only model-free epoch-2 materialization after this boundary
and synchronized state are exact on origin.
