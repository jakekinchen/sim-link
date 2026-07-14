# Slice Brief 121 - T20.1 Simulation-Only Training Specification And Authority

**Date:** 2026-07-14

## Objective

Create the first model-readable, simulation-only training specification from
the verified T17.5b raw grasp store and convert the owner's explicit training
grant into a mechanically recomputed central-authority decision.  This slice
does not train or load a model.

## Contract

- Select a fixed one-to-three-episode train/evaluation split from the
  append-only T17.5b raw store.  Verify every selected source record and bind
  its content hash, source phase, actor-safe observations, and measured action
  variant; do not rewrite the raw records.
- Materialize only a bounded local training input for the selected simulation
  episodes.  Bind its exact state/action normalization statistics, canonical
  coordinate representation, source-window provenance, and no-privilege
  actor schema in a signed T20.1 specification.
- Add an explicit, content-addressed owner grant as a required prerequisite of
  `simulation_training_ready`.  Its scope is this T20.1 simulation-only
  specification and it grants neither physical transfer nor promotion.
- The production authority request must mechanically bind the verified
  structural, executable-stack, coordinate, normalization, compiler, and
  simulation-property evidence.  The central composer, not any component,
  must grant `simulation_training_ready`.

## Acceptance Criteria

- A rerun deterministically reproduces the T20.1 specification and its
  source/normalization identities; source-hash drift, extra episodes, actor
  privilege, derived-action substitution, non-finite values, missing owner
  grant, expired grant, or altered authority evidence fails closed.
- The production decision independently recomputes from its request and grants
  only `simulation_training_ready`; physical-transfer and promotion decisions
  remain withheld.
- `project_state.json` and the active ledger advance to T20.2 only after the
  decision is verified and locally committed/pushed.  No model, optimizer,
  physical hardware, external compute, or Brev action occurs in this slice.

## Out Of Scope

ACT/PI0.5 model load, optimizer updates, policy evaluation, hardware access,
physical motion, Brev, external compute, checkpoint promotion, or deletion.
