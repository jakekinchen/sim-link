# Slice Brief 122 - T20.2 Bounded ACT Overfit

**Date:** 2026-07-14

## Objective

Run the first local, simulation-only ACT overfit against the verified T20.1
three-episode source-bound tensor view. Establish whether optimizer updates
produce near-zero training error and a distinct, held-out closed-loop action
behavior.

## Contract

- Require the live T20.1 authority verifier immediately before loading the
  runtime or optimizer. It must reject an expired owner grant, source drift,
  or a non-simulation decision.
- Use only the 488-frame train split and 244-frame held-out split bound by the
  T20.1 tensor-view hash. Do not rewrite raw source bytes, train on the held-out
  split, use privileged fields, access hardware, external compute, or Brev.
- The ACT model must consume the actor-safe observations and predict an action
  chunk from the measured-action target. Record exact loss, finite-gradient,
  optimizer-update, weight, and input identities.
- Evaluate the saved model separately on both splits. A small supervised loss
  is not task success: any closed-loop rollout remains a simulation evaluation
  with outcome and strict-success semantics recorded separately.

## Acceptance Criteria

- The run is reproducible from a bounded local config and records whether the
  optimizer ran, all losses/gradients are finite, and training error changed
  from the untrained baseline. Source/output hash or authority drift fails
  closed.
- A new simulation evaluation records a policy-generated action sequence and
  reports terminal outcome separately from strict semantic success. It must not
  claim physical transfer, promotion, or policy acceptance.

## Out Of Scope

PI0.5, model bake-offs, MPS ladders beyond this overfit, physical hardware,
external compute, Brev, checkpoint promotion, or destructive cleanup.

## Verification Result

The bounded 100-update run reduced train L1 from 1.0217032432556152 to
0.16815676142772037 and produced held-out L1 0.22133693750947714. This is a
real finite optimizer change, but not near-zero overfit.

The saved model then owned all 244 controls in a fresh held-out-seed MuJoCo
rollout. It used no assist and required no action projection, but formed zero
strict-v2 grasp contacts and lifted the object only 0.0002023007066939697 m
against the 0.025 m gate. The terminal outcome is
`no_strict_grasp_contact`; semantic strict success, policy acceptance,
physical transfer, and promotion all remain false. Five 256 px rendered
keyframes and measured-versus-threshold margins preserve the negative proof.
