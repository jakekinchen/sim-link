# Slice Brief 089 - Strict Anchor Grasp Evaluator

**Date:** 2026-07-13

## Objective

Begin the Minimum Viable Grasping Twin with one executable grasp-specific
semantic gate and positive/adversarial analytic trajectories around the visible
lightweight turquoise anchor candidate.

## Contract

- Bind the current physical observation only to visible appearance and source
  frame identity. Keep physical dimensions, mass, COM, friction, pose, and
  camera transform explicitly awaiting measurement.
- Define one separate nominal simulation anchor cousin; never relabel its
  declared geometry or mass as physical measurement.
- Require the ordered phases `approach`, `pregrasp`, `close`,
  `grasp_confirmed`, `lift`, `stable_hold`, `lower`, `release`, and `retreat`.
- Evaluate object identity, fingertip contact, table clearance, relative grasp
  drift, stable hold, speed, impact, current, forbidden collisions, release,
  and retreat through one deterministic evaluator.
- Reject pushing, sliding, hooking, table pinning, throwing, teleport, scripted
  object motion, momentary contact, wrong object, missing/reordered phases,
  controller assistance relabeled as pure policy, and evaluator-state leakage.
- Run the analytic positive and every negative through the same evaluator and
  write one signed deterministic fixture.

This slice proves strict grasp-evaluator behavior on analytic simulation traces
only. It grants no MuJoCo trajectory validity, physical object profile, policy
success, training authority, physical motion, or twin qualification.

## Verified Outcome

- Checked artifact:
  `configurations/robot_lab/strict_anchor_grasp_evaluator.fixture.json`.
- Artifact identity: `4f0bad3c9f12fc648a7eed25a9f9fcaf7b8a1c63ca312e3a13f2c20d0f3120d8`.
- File SHA-256: `3be8ac16710b857e302b341b8e563feac56c6ed6238683abee0704cc7a6fb418`.
- One analytic-expert trace satisfies the declared semantics but is not labeled
  pure-policy success.
- All twelve adversarial traces fail through the same evaluator for their
  expected reason.
- Malformed non-finite, negative safety, boolean contact-count, and non-boolean
  safety fields fail closed.
- The physical observation retains null dimensions, mass, COM, friction, and
  pose transform; the nominal analytic cousin claims no physical measurement.
- Six focused tests pass in both repository runtimes. A 66-test relevant broad
  gate passes. A larger 99-test invocation completed 98 tests but its one
  LeRobot provenance test could not import Torch from the MuJoCo-only runtime;
  no product failure was hidden by that environment limitation.
