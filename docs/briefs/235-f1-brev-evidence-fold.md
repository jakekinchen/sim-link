# Slice Brief 235 - F1 Brev Evidence Fold

**Date:** 2026-07-17

## Objective

Fold the completed, off-ledger F1 Brev experiment into the canonical project
spine without running training, inference, simulation, hardware, or external
compute. Verify the exact compact receipts in
`/Users/kelly/Documents/Codex/2026-07-17/sim-link-f1-pi05-brev`, retain only a
small signed evidence pointer, and record F1 honestly as one completed PI0.5
full-fine-tune negative with no Gate C pass and no gateway result.

This is a historical evidence-reconciliation support slice. It must not reopen
or change the completed F0, F0c, F2, or F3 routes; move the annotated freeze
tag; import bulk checkpoint, model, output, or external-clone bytes; create or
resume a Brev resource; or grant training, rollout, hardware, transfer,
promotion, or gateway authority.

## Source boundary

- Canonical starting commit: `4fe7f685d63e72c21bcf2b1aa3c071bf86ba3a88`.
- Off-ledger source root:
  `/Users/kelly/Documents/Codex/2026-07-17/sim-link-f1-pi05-brev`.
- Required source receipts: `receipts/RUN_RECEIPT.json`,
  `outputs/evaluations/EVALUATION_SUMMARY.json`, all ten fixed-checkpoint
  rollout JSONs, `receipts/SPEND_LEDGER.json`, and
  `receipts/TEARDOWN_INVENTORY_RECEIPT.json`.
- Retained checkpoint remains outside Git at
  `/Volumes/cerebro/CodexOffload/f1-pi05-r0-20260717/checkpoint-001000/pretrained_model`.
- Frozen F0c spec identity `6a178138...`, post-freeze export `dce41616...`, F3
  manifest `ec9084dc...`, and freeze-tag target `04a52929...` are immutable.

## Required verification

1. Recompute canonical identities for the run, preflight, launch, evaluation
   summary, spend, teardown, and all ten rollout receipts.
2. Confirm one 5,000-step full fine-tune, five checkpoints, two action-cadence
   variants, ten strict-v2 rollouts, and zero strict successes.
3. Confirm the frozen selection is checkpoint 1,000/chunk-50 at
   `0.03751930418757199` m maximum lift, failing only
   `grasp_hold_strict_v2`.
4. Directly hash the retained model and config without deserializing tensors;
   require `7555449565...` and `1f17178a8b...` respectively.
5. Confirm the displayed-rate spend calculation is `$5.526`, delete request
   `06:10:23` CDT, deletion confirmation `06:10:58`, and final inventory
   `06:11:07` with zero resources.
6. Run a fresh authenticated `brev ls --json` before closeout. If an
   unexpected idle resource exists, apply the repository cost-control rule;
   otherwise perform no Brev mutation.

## Deliverables

- One compact signed F1 evidence pointer containing exact receipt/file
  identities, result facts, checkpoint location/hashes, and closed authority
  flags.
- Minimal updates to `project_state.json`, `GOAL.md`, the active ledger, and
  materially stale reconstruction/documentation statements.
- One same-agent reviewer decision and one session closeout.
- Focused pointer tests plus relevant documentation, project-state, and
  reconstruction-kit invariants.

## Acceptance

The fold passes only when every source identity and result fact is independently
verified, the retained checkpoint hashes match without adding its bytes to Git,
the live Brev inventory is empty, F1 is labeled a completed negative/no-Gate-C
result, all authority remains fail-closed, scoped tests and adversarial review
pass, and the exact closeout commit is preserved on
`origin/codex/pi05-autolearn-loop`.
