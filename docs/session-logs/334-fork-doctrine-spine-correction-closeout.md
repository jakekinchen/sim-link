# Session 334 - Fork Doctrine Spine Correction Closeout

**Date:** 2026-07-17
**Task:** K4 / Brief 236
**Reviewer:** 329

## Outcome

Implementation `99c13d0...` carries the corrected RoboTTT/GR00T review doctrine
from annex amendment `aae542a...` into the living reconstruction forward plan,
architecture, results/lessons, and day-one runbook. PI0.5 remains the primary
NVIDIA experiment; native pinned-LeRobot GR00T is the bounded challenger, while
the standalone path alone requires V3-to-V2 plus `modality.json`.

The temporal ladder now uses a Markov-augmented candidate and an explicitly
implemented short history wrapper before learned memory. Corrective episodes
branch before causal failure, preserve causal and terminal frames, restore full
simulator dynamics state, and require expert replanning. Training receipts are
immutable, cite `doctrine_commit`, and cannot self-promote; a separate evaluator
artifact owns promotion and joins by `candidate_id`.

## Verification and review

Read-only source inspection at pinned LeRobot `e40b58a8...` confirms native
`groot`, v3.0 dataset semantics, and ACT's `n_obs_steps != 1` rejection. Fourteen
reconstruction-kit tests, twenty-one documentation/state tests, frozen manifest
check `ec9084dc...`, JSON/link/whitespace checks, and stale-phrase search pass.

Same-agent review also removes the residual absolute sim2real claim, clarifies
that ACT/state-RL are demo-critical while PI0.5 is NVIDIA-primary, and fixes the
receipt/evaluator direction in the architecture. The learned hybrid is labeled
the strongest simulation fallback and only a gated physical candidate.

## Authority

`sim2claw-genesis`, the frozen reconstruction manifest, source selection, and
signed F0c spec are unchanged. No training, model action, rollout, data
conversion, package install, network access, hardware, external compute, Brev
operation, transfer, promotion, or destructive action occurred. K4 closes as a
documentation-only verified support task.
