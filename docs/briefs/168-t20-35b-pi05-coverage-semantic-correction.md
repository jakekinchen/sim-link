# Slice Brief 168 - T20.35b PI0.5 Coverage Semantic Correction

**Date:** 2026-07-15

**State:** `verified`

## Objective

Correct T20.35a's generic five-pathway expectation against the pinned PI0.5
implementation before authorizing the no-LoRA capacity ceiling.

## Contract

- Bind the pinned LeRobot revision, patch set, and exact
  `policies/pi05/modeling_pi05.py` content identity.
- Mechanically establish PI0.5's real adaptation modules:
  `action_in_proj`, `action_out_proj`, `time_mlp_in`, and `time_mlp_out`.
- Prove that PI0.5 intentionally has no `state_proj`; do not relabel its
  absence as a coverage failure.
- Prove that the default PEFT regex requests the stale names
  `action_time_mlp_in/out`, while the implementation uses `time_mlp_in/out`.
- Recompute the exact saved-adapter coverage decision against the four real
  modules, preserving the immutable T20.35 evidence and superseding only the
  incorrect T20.35a pathway semantics.
- Run no model, inference, optimizer, dataset, or checkpoint mutation.

## Acceptance Criteria

- Deterministic tests reject source identity, real-module set, stale-name
  mapping, tensor, pairing, finiteness, and derived-decision drift.
- One corrected signed audit distinguishes intentional `state_proj` absence
  from the genuine missing `time_mlp_in/out` coverage.
- Same-agent adversarial review, canonical state, ledger, plan, session log,
  reviewer decision, scoped commits, and remote preservation agree before any
  T20.35c training authority.

## Out Of Scope

Changing upstream LeRobot; changing the PEFT regex; model construction;
inference; optimizer training; the expert-only capacity run; learning-rate or
budget rungs; Gate C work; hardware; external compute; Brev; transfer; or
promotion.

## Result

Correction `446a0686...` binds pinned source `b05b6afe...` and proves PI0.5's
real modules are action in/out plus `time_mlp_in/out`; `state_proj` is
intentionally absent. The default PEFT names include nonexistent `state_proj`
and stale `action_time_mlp_in/out`, so the adapter genuinely misses both real
time-MLP layers. T20.35a's generic five-pathway decision is superseded while
its tensor enumeration remains immutable. The corrected evidence still routes
to the separately authorized no-LoRA expert-only capacity ceiling.
