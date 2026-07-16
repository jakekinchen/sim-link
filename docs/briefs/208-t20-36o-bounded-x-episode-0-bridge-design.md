# Brief 208 - T20.36o Bounded X Episode-0 Bridge Design

## Status

Active model-free design/authority slice under the owner's 2026-07-16
continuation and priority-3 direction. T20.36n is verified mixed-negative by
Reviewer 266. Gate C route is open; Gate C execution remains closed.

## Objective

Freeze the exact episode-0 PI0.5 execution semantics, source windows, target
masks, deterministic probe identities, correction/replay schedule, finite
update ceiling, and pass/stop rules needed to make X eligible for a separately
authorized one-episode Gate C rollout. This boundary may inspect signed source
artifacts and cached dataset records but may not construct a model or optimizer.

## Frozen Execution Contract

- Use a new Gate C contract with `n_action_steps=50`; the T20.32 legacy
  `ACTION_HORIZON=5` adapter contract is explicitly ineligible.
- Reset `PI05Policy`'s action queue exactly once immediately before the
  244-frame rollout. `select_action` may sample only when that queue is empty
  and then executes one queued action per environment frame.
- The only chunk-start frames are `[0, 50, 100, 150, 200]`.
- The corresponding executed lengths are `[50, 50, 50, 50, 44]`.
- Bind each start to its exact episode-0 source frame identity, phase, state,
  images, task, and 50-step target window before any optimizer creation.
- At start 200, target and acceptance masks contain 44 true and six false
  positions. The six unexecuted tail predictions are excluded from loss
  acceptance, amended-gate decisions, and actor-valid evidence; they remain
  reportable only as non-executed diagnostics.
- Bind five deterministic probe seeds per start before training. No
  post-result seed substitution is allowed.

## Bridge Design Requirements

1. Mechanically derive the five starts and masks from rollout length 244 and
   queue size 50; reject conflicting horizon, reset, padding, or cadence data.
2. Record the local `PI05Policy.select_action` source revision and file hash
   that establish queue-empty sampling and one-action popping.
3. Freeze the exact five observation/target records and their byte/content
   identities. Missing frame, phase, image, state, target, or mask evidence
   fails closed.
4. Extend X's physical-Jacobian/time-weighted correction only across these
   five bound states. Preserve paired standard replay so a bridge cannot trade
   source-batch competence for downstream chunk-start competence.
5. Derive the finite correction set as five starts by five probe seeds by ten
   denoise steps (`250` examples) and pre-register deterministic ordering,
   source-replay ratio, update ceiling, mid-run probes, selection rule, and
   first-complete-pass stop before optimizer creation.
6. Frozen amendment `463477dc...` must pass at every executed joint/timestep
   for every registered probe at all five starts. The original uniform metric
   remains reported but non-gating. Any non-finite value, source-replay
   regression, identity drift, or unmasked tail use fails closed.
7. A pass grants no Gate C execution by itself. It only permits a separate
   central request, preflight, one-episode permit, reviewer decision, and
   remote-preserved boundary.

## Required Deliverables

- Deterministic execution/window spec generator and exact verifier.
- Tests for starts, lengths, queue-reset count, horizon rejection, final-tail
  mask, source identities, probe uniqueness, and failure on stale or missing
  evidence.
- Model-free update-budget/replay critique with one frozen selection rule.
- Central training-authority request and preflight in a later separately
  reviewed boundary; no model or optimizer action in this slice.

## Prohibited Actions

No model construction/load/inference, optimizer creation/training, checkpoint
mutation, Gate C rollout, threshold change, candidate substitution, physical
hardware, network/download, external compute, or Brev.
