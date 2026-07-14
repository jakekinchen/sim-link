# Slice Brief 146 - Sim-Link MVP Cut And Local Task Queue

**Date:** 2026-07-14

## Objective

Reconcile the SO-101 program documentation with the owner-approved MVP triage,
remove stale Robo Scan sequencing, and establish one dependency-ordered
sim-link-only queue for the period before Robo Scan produces a real metric
capture.

## Contract

- Treat the accepted triage as the product cut: the immediate long pole is a
  clean `pi05_base` dataset-native T20.17 campaign, not a new architecture.
- Preserve the thin governance shell over pinned LeRobot and MuJoCo. Keep Robo
  Scan as a separate immutable artifact producer; do not merge repositories or
  create a third hardware-runtime repository.
- Record the three mutable learning surfaces separately: workcell twin, robot
  policy, and optional learned dynamics. The MVP may update only the policy and
  a small explicit twin ensemble; world models and residual dynamics are cut.
- Pull forward only cheap, causal primitives: existing MuJoCo state branching,
  observer-role separation, a discrete uncertainty ensemble, an
  observable-only evaluator, a thin paired trace runner, and timing evidence.
- Correct the integration roadmap to record Robo Scan producer commit
  `72eb02e`, verified sim-link I2/I3 intake, and the I4 metric-bundle wait state.
- Define tasks only for sim-link. The arriving USB cable is context for the
  separate Robo Scan lane and grants no camera, hardware, motion, training,
  external-compute, or Brev authority here.
- Preserve all unrelated dirty files and historical evidence. Make no source,
  fixture, model, output, hardware, or external-compute change.

## Acceptance Criteria

- Architecture, decisions, requirements, documentation routing, and the
  integration roadmap agree on the MVP cut and repository boundaries.
- One canonical task list names dependency order, outputs, verification gates,
  deferrals, and the MVP exit condition without duplicating live authority.
- `GOAL.md`, the active ledger, and `project_state.json` point to T20.17 as the
  immediate sim-link task and record later tasks as pending rather than active.
- Stale claims that Robo Scan Brief 054 is dirty or that sim-link still waits to
  start I2 are removed from living documents; append-only history remains
  unchanged.
- Documentation link tests, JSON parsing, workflow audit, and targeted stale
  reference searches pass.

## Out Of Scope

Optimizer execution; dataset generation; model inference; simulation rollout;
Robo Scan edits; camera or robot access; paid or external compute; Brev; I4/I5
metric workcell compilation; implementation of the queued source-code tasks;
or any transfer, promotion, or physical proof claim.
