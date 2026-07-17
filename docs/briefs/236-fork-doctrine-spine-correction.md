# Slice Brief 236 - Fork Doctrine Spine Correction

**Date:** 2026-07-17

## Objective

Reconcile the owner-approved technical corrections to commit `1018b4e` across
the fork's living execution spine. Treat the already-pushed annex amendment
`aae542a0a2f66328e0e8b88877eb6c467340579d` as the corrected source and carry
its executable consequences into the reconstruction forward plan,
architecture, results/lessons, and day-one handoff surfaces.

This is a documentation and invariant-test support slice only. It must not
change the immutable `sim2claw-genesis` source boundary, regenerate the frozen
reconstruction manifest, alter F0c's signed experiment contract, open a model
or optimizer, run a rollout, access hardware, start external compute or Brev,
or grant transfer or promotion authority.

## Required corrections

1. Keep the release-fixed PI0.5 continuation as the primary NVIDIA experiment;
   treat GR00T N1.7 as a bounded challenger. Try the pinned-LeRobot native
   `groot` path on LeRobot v3 data first; require V3-to-V2 conversion plus
   `modality.json` only for the standalone Isaac-GR00T fallback. Both paths
   require exact camera, action, gripper, language, image, horizon,
   normalization, and processor compatibility.
2. Preserve the temporal-observability ladder as F0c, a
   Markov-augmented-state candidate, an explicitly implemented two-to-four-step
   state/action history wrapper, then a small recurrent model only if the
   simpler rungs fail. The pinned ACT rejects `n_obs_steps != 1`, so history is
   not a configuration-only experiment.
3. Define correction episodes from the diagnosed causal intervention point,
   retain both causal and terminal frames, restore dynamics-relevant simulator
   state, and require the expert to replan from the branch. For one-observation
   ACT, describe these as policy-induced corrective starts rather than literal
   failed-prefix context.
4. Keep training receipts immutable and non-promoting. Record
   `parent_checkpoint`, `hypothesis_id`, `candidate_id`, `doctrine_commit`, and
   a nullable `evaluation_decision_ref`; place `promotion_decision` only in a
   separately signed evaluator-owned artifact joined by `candidate_id`.
5. Describe the learned/scripted Level-2 hybrid as the strongest simulation
   fallback and only a physical candidate after gateway, calibration, shadow
   mode, and a bounded canary. Keep explicit state-based primitives as the most
   reliable physical fallback until then.

## Deliverables

- Consistent corrected language in the annex, `reconstruction-kit/FORWARD_PLAN.md`,
  `reconstruction-kit/ARCHITECTURE.md`,
  `reconstruction-kit/RESULTS_AND_LESSONS.md`, and the day-one handoff runbook.
- A focused text invariant that rejects the two original technical errors and
  requires the evaluator-owned decision split.
- Minimal canonical project-state, goal, active-ledger, reviewer, and session
  closeout updates.

## Acceptance

The slice passes only when the five corrections agree across the living spine,
the frozen source tag/manifest and signed F0c contract are unchanged, focused
and relevant documentation tests pass, a fresh same-agent adversarial review
finds no authority escalation or evidence relabeling, and the scoped closeout
commit is present on `origin/codex/pi05-autolearn-loop`.
