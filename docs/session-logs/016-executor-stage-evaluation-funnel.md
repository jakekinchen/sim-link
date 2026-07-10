# Executor Session 016 - Stage Evaluation Funnel

**Date:** 2026-07-10

## Slice

Complete T12.1 by measuring reach, contact, grasp, lift, transport, release, and
placement for every rollout and aggregating those rates across evaluation seeds.

## Result

- Every recorded frame includes gripper position alongside all cube transitions.
- Episode summaries report stage counts, rates, cube identities, and minimum
  gripper-to-any-cube distance.
- Evaluation summaries average the seven stage rates and report how many episodes
  actually supplied stage metrics.
- Reach is evaluated against every cube, not only the current language target.

## Verification

- 59 intervention/autolearn tests pass.
- A bounded MPS seed-7300 policy-only control smoke executed 400 neural frames.
- Corrected recomputation reports reach 2/4, contact 2/4, and grasp/lift/transport/
  release/placement 0/4, matching its terminal 0/4 failure.
- The first computation incorrectly measured reach only against the instructed
  cube and produced contact without reach. That inconsistency was detected and fixed.
- Physical follower commanded remains false.

## Proof Boundary

The launcher's `policy_gripper` mode may enable contact-gated grasp stabilization.
T12.2 must not label that mode strict merely because no task-space controller ran.

## Next Step

T12.2 explicit proof-mode classification and promotion gates.
