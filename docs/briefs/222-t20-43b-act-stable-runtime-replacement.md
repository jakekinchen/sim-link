# Slice Brief 222 - T20.43b ACT Stable-Runtime Replacement

**Date:** 2026-07-16

## Objective

Implement and fixture-test the exact one-time ACT replacement authorized by
owner addendum `8b4a206`: preserve the frozen T20.43 recipe, replace only the
failed renderer/runtime boundary with the stable T20.44 interpreter and real
renderer-entrypoint smoke, and define fresh Gate A, central authority,
preflight, one-use permit, marker, evidence, terminal-result, and independent
verification contracts. Commit, push, and review this implementation before
materializing live authority or reading any model tensor.

## Frozen source and authority boundary

- Bind T20.44 terminal result `9d916206...`, Reviewer 297, compact closeout
  commit `9869cba`, and synchronized state commit `b24ac30`. T20.44 remains a
  terminal negative and is not modified or retried.
- Bind owner addendum `8b4a206`, which supersedes T20.43's no-replacement rule
  exactly once and only after the T20.44 terminal state is exact on origin.
- Bind original ACT spec `b3a510f8...`, implementation `9a03a86`, Reviewer
  291, and T20.43 terminal receipt `b64ec6d0...`. The zero-update checkpoint-0
  rollout is infrastructure evidence only and is not a trained ACT result.
- Bind exact R0 result `d238379b...`, mixture `37b30d34...`, statistics
  `02ba0e70...`, retention `19d19fba...`, 129 episodes, and 31,366 frames.
  Existing seeds 6-7 and all fresh held-out rows remain outside training and
  fitted statistics.

## Recipe invariance

- Preserve the complete original ACT recipe without semantic changes: fresh
  ACT initialization, cached ResNet-18 ImageNet backbone, batch 8, seed
  `20260801`, AdamW at `1e-5` for policy and backbone, weight decay `1e-4`,
  gradient clipping 10.0, no scheduler, no AMP, no compilation, and exactly
  10,000 maximum optimizer updates.
- Preserve checkpoints `[0,500,1000,2500,5000,7500,10000]`, chunk size and
  training action steps 50, one observation step, two R0 cameras, six state/
  action dimensions, MEAN_STD processors, episode-aware shuffled sampling,
  and no weighting, correction objective, sweep, or held-out ingestion.
- Preserve rollout-primary evaluation of nominal episode 0 at every checkpoint
  under chunk-50 and receding-10 semantics. Strict-v2 alone selects the first
  pass; chunk-50 wins a same-checkpoint tie. Continue through 10,000 finite
  updates while retaining the first pass if one occurs.

## Stable runtime and renderer correction

- Use exact stable interpreter `external/lerobot/.venv/bin/python` plus the
  already-bound cached MuJoCo 3.3.5 support tree from T20.44. No temporary
  interpreter, package installation, environment mutation, or network access
  is allowed.
- Before any attempt marker or backbone tensor read, run the real
  `render_rollout_mirror.py` entrypoint through that exact interpreter on the
  retained T20.43 trace `6133ce58...`. Require exit 0, MuJoCo 3.3.5, a valid
  nonempty MP4 and manifest, exact trace/output hashes, and a dedicated,
  absent, unaliased T20.43b smoke path.
- The future ACT runner and every mirror subprocess must use the same exact
  interpreter and support-tree binding. Any mismatch, fallback, missing
  dependency, output collision, or stale smoke fails before the marker.

## Fresh authority and one-use boundary

- Implement task-specific Gate A, owner grant, central request/decision,
  runtime preflight, one-use permit, signed pre-run acceptance, exclusive
  marker, result, scorecard, retention, and terminal-failure artifacts.
- Gate A must reconstruct R0 counts/order/features/statistics/held-out
  exclusions, ACT processors, action inverse, coordinate round trip, cached
  backbone bytes, source hashes, and stable renderer smoke without model
  construction or tensor deserialization.
- Implementation must be reviewed on origin before any live materialization.
  Materialized Gate A/smoke/authority must then be reviewed on origin before
  the marker. The marker precedes backbone reads, model construction,
  inference, optimizer creation, and Gate C execution.
- The first marker consumes the only T20.43b replacement. Every later failure
  is signed and terminal. No second replacement, retry, continuation, or
  adaptive checkpoint may follow.

## Evidence and verification

- Retain complete proposed/applied/state/object/contact traces, decode/action
  hashes, first source divergence, strict-v2/T20.38 margins, report-only
  amended/uniform analyses, queue/tail accounting, and signed MP4 manifests
  for both execution variants at every checkpoint.
- Keep checkpoint, rollout, and mirror trees local with signed identities;
  track only compact authority/result/scorecard/retention evidence.
- Tests must reject recipe drift, stale R0/source/cache/smoke/authority,
  interpreter mismatch, output aliases, marker-order violations, non-finite
  training, missing checkpoints, queue/tail errors, strict-v2 spoofing,
  first-pass replacement, evidence hash drift, retry, and authority
  escalation. Run focused and relevant broad regressions, strict JSON,
  compilation, lint/format, pointer, whitespace, and fresh same-agent review.

## Authority withheld

This brief opens implementation and fixture tests only. It grants no live
renderer smoke or authority materialization, attempt marker, backbone/model
tensor read, model construction/load/inference, optimizer creation/training,
checkpoint, learned-policy rollout, Gate C/D/E claim, retry, second
replacement, recipe/schedule/threshold change, correction objective, archive
replay, T20.45 activation, hardware/camera/serial access, physical motion,
network/download, package installation, external compute, Brev, transfer,
promotion, or destructive operation.

## Implementation boundary

Spec `13c5bb4b...` and the complete T20.43b contract/materializer/runner/CLI/
test implementation preserve the original signed campaign, ACT configuration,
dataset, and evaluation objects exactly. The only operational correction is
the stable T20.44 interpreter plus cached MuJoCo support tree and a fresh real
renderer smoke that binds trace identity `6133ce58...` and trace-file SHA
`f9dc0e6d...` before any marker. Eleven focused, 30 targeted/regression, and 34
pointer/composer/receipt tests pass; offline lint/format, compilation, strict
spec reconstruction, CLI import, JSON, and whitespace checks pass. Reviewer
299 opens model-free materialization only after this implementation is exact on
origin. No live smoke, authority, marker, model, optimizer, or rollout action
has occurred.
