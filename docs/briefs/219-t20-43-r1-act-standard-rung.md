# Slice Brief 219 - T20.43 R1 ACT Standard Rung

**Date:** 2026-07-16

## Objective

Implement and fixture-test the exact R0 Gate A parity, official full ACT
standard-recipe configuration, fixed checkpoint/evaluation schedule, complete
strict-v2 trace/video evidence, central authority, runtime preflight, one-use
permit, and immutable result contracts for one bounded local-MPS R1 attempt.
Commit, push, and review that implementation before materializing any live
authority or constructing a model.

## Frozen source boundary

- Bind origin commit `f46c8aae0a0dc291ebc80ec1094033311fa0f717` and
  Reviewer 290.
- Bind R0 result `d238379b...`, mixture `37b30d34...`, statistics
  `02ba0e70...`, retention `19d19fba...`, and the locally retained package
  manifest `bd36b7c4...` / file `6b7abd88...`.
- Require the package root to load as exactly 129 episodes and 31,366 frames,
  with the exact ten T20.23 base episodes once plus 119 R0 training successes.
  Fresh-held-out candidates and existing held-out seeds 6-7 remain outside
  training and fitted statistics.
- Bind LeRobot source commit `e40b58a8...`, the exact ACT/config/processor/
  dataset source files actually used, local dependency versions, and the
  cached ImageNet ResNet-18 bytes `f37072fd...` (46,830,571 bytes). No network
  or fallback is allowed.

## Exact standard recipe

- Fresh `ACTPolicy`; no prior ACT checkpoint or adapter is loaded. The official
  cached ImageNet backbone initialization is allowed and is not an ACT policy
  checkpoint.
- Full LeRobot ACT defaults except dataset-bound features, device, horizon, and
  explicit serialization controls: two 3x256x256 camera inputs, six-joint
  state/action, one observation, chunk 50, training `n_action_steps=50`,
  MEAN_STD visual/state/action processing, ResNet-18, model width 512, eight
  heads, feed-forward width 3,200, four encoder layers, one decoder layer,
  VAE enabled with latent 32/four VAE encoder layers/KL weight 10, dropout 0.1,
  float32, MPS, and no compilation or mixed precision.
- Official AdamW preset: learning rate `1e-5`, backbone learning rate `1e-5`,
  weight decay `1e-4`, no scheduler, gradient clipping at 10.0, batch size 8,
  deterministic seed `20260801`, shuffled fresh batches, and exactly 10,000
  maximum optimizer updates. No sample weighting, correction objective,
  oversampling, held-out ingestion, sweep, or retry.
- Fixed checkpoint/evaluation schedule:
  `[0, 500, 1000, 2500, 5000, 7500, 10000]`. Save each checkpoint as an
  immutable local tree with a signed identity. Continue the one run to 10,000
  finite updates even if a checkpoint passes; immediately freeze and render
  the first valid Gate C evidence when it appears.

## Gate A and rollout-primary evaluation

- Before model construction, reproduce the R0 manifest/tree identities,
  dataset feature/order/count contract, package metadata statistics, compact
  training-only statistics, fixed sample tensors, processor outputs, action
  postprocessor inverse, and dataset<->MuJoCo coordinate round trip. Missing,
  non-finite, reordered, held-out-contaminated, or mismatched evidence fails
  before the marker.
- Gate A is parity evidence only. No one-batch or open-loop reconstruction
  threshold may block safe simulation rollout evaluation.
- At every scheduled checkpoint, run the unchanged nominal training episode 0
  for 244 frames under both pre-registered semantics:
  1. chunk-50: one queue reset, decode starts `[0,50,100,150,200]`, executed
     lengths `[50,50,50,50,44]`, six unexecuted tail actions excluded;
  2. receding-10: one queue reset, decode starts
     `[0,10,...,230,240]`, executed lengths 24 tens plus a final four, and
     every unexecuted chunk tail excluded.
- Strict-v2 is the only success oracle. Gate C is the first scheduled
  checkpoint whose unassisted episode-0 rollout passes strict-v2 under either
  consumption variant. If both pass at the same checkpoint, chunk-50 is the
  deterministic selection tie-breaker. Neither variant changes the oracle.
- Every rollout retains the complete proposed/applied/state/object/contact
  trace, first source divergence, strict-v2 margins, T20.38 receipt margins,
  amended-gate `463477dc...` analysis, report-only uniform 0.05-rad analysis,
  action/decode hashes, queue/decode starts, and a signed mirror MP4 manifest.
  The first Gate C pass is frozen immediately; later checkpoints cannot replace
  its demo-selection priority.

## Authority and one-attempt boundary

- Implement a task-specific owner grant, central composer request/decision,
  no-write live preflight, one-use permit, pre-run acceptance, marker-first
  runner, full verifier, terminal-success/negative result, and retention
  receipt.
- Implementation must be committed, pushed, and accepted by a fresh same-agent
  review before authority materialization. Materialized authority and Gate A
  must then be committed, pushed, and separately accepted before the marker.
- The marker precedes pretrained-backbone deserialization, ACT construction,
  inference, or optimizer creation. Once written, it consumes the sole attempt.
- Checkpoint and rollout trees remain local with signed tree identities; compact
  specs, decisions, results, scorecards, and MP4 manifests are tracked.

## Verification

- Tests first cover R0/source/cache/dependency/branch/remote drift, held-out
  leakage, feature/statistics/order mismatch, coordinate/processor parity,
  unsafe ACT defaults, schedule mutation, non-finite loss/gradient, duplicate
  or missing checkpoint, queue-reset/decode-start/tail masking, variant
  confusion, strict-v2 spoofing, first-pass replacement, trace/video identity
  drift, output aliases, stale authority, marker ordering, retry, and every
  prohibited authority field.
- Run focused tests, relevant ACT/dataset/closed-loop/strict-v2/receipt/renderer
  regressions, Ruff, compilation, strict JSON, project-pointer, scoped-diff,
  remote-preservation, and two fresh same-agent adversarial reviews.

## Authority withheld

This brief opens implementation and fixture tests only. No live authority
artifact, Gate A runtime artifact, attempt marker, cached backbone tensor read,
model construction/load, inference, optimizer creation/training, checkpoint,
learned-policy rollout, Gate C/D/E claim, retry, correction objective, Gate B
entry barrier, threshold change, archive replay, hardware/camera/serial access,
physical motion, network/download, external compute, Brev, physical transfer,
promotion, destructive operation, R2 activation, or second architecture.
