# Brief 204 - T20.36k Consequence-Calibrated Gate B Amendment Design

## Objective

Design, without model construction or training, the owner-pre-authorized Gate B
amendment path after both ACT and SmolVLA memorize the objective but fail the
uniform 0.05-rad decoded-action criterion. Derive task-consequence sensitivity
from bounded simulation perturbations of the canonical target trajectory, keep
the strict uniform metric visible as report-only, and make one-episode Gate C
closed-loop reproduction the eventual behavioral arbiter.

## Pre-Registered Owner Decision

Before the T20.36j result existed, the owner authorized the branch: after the
single licensed fix/controls, stop the model alphabet; examine the frozen gate;
use task-consequence-weighted per-joint criteria while retaining the strict
uniform metric; and make one-episode closed-loop behavior decisive. T20.36e/f
already provide the ACT control/localization and T20.36j provides the SmolVLA
track. Neither may be retried.

## Required Work

1. Bind the exact ACT and SmolVLA result identities, canonical action chunk,
   strict-v2 task phases, and unchanged historical Gate B.
2. Define bounded, symmetric per-joint/time perturbations independently of all
   candidate error magnitudes.
3. Run model-free simulation sensitivity on the canonical episode or its exact
   replay surface and record consequence deltas for reach, grasp, lift, hold,
   lower, release, retreat, contact, and safety predicates.
4. Derive weights/threshold classes only from those consequence deltas with
   explicit floors so shoulder lift, gripper, and other task-critical joints
   cannot be waived.
5. Keep the uniform 0.05-rad maximum, objective ratio, deterministic hashes,
   and per-joint/time errors reported. The amendment may alter gating only in a
   later separately reviewed artifact.
6. Specify the one-training-episode Gate C arbiter and fail-closed relationship:
   a consequence-metric pass alone never accepts a policy.

## Acceptance

- Candidate outputs are not inputs to threshold derivation.
- Sensitivity is deterministic, symmetric, phase-aware, and content-addressed.
- Task-critical errors remain bounded; task-irrelevant freedom is evidenced,
  not asserted.
- The artifact is non-authorizing and cannot relabel T20.36e or T20.36j.
- No model, optimizer, rollout, Gate C execution, hardware, external compute,
  or Brev action occurs.

## Prohibited Actions

ACT/SmolVLA retry, model construction/inference, optimizer training, immediate
Gate B amendment, fitting thresholds to candidate errors, Gate C execution,
policy selection/promotion, hardware, external compute, or Brev.

## Verified Result

Result `a3b391784eaca8fef2cb9ff6abe45cc21346cada8f9483be60692dac0faf1f66`
binds 252 symmetric pairs across six joints, seven phase groups, and six fixed
magnitudes. The canonical replay passes all strict-v2 gates; 202 pairs pass and
50 fail, with zero non-monotonic cells. Wrist roll is insensitive through
0.4 rad in every phase, while shoulder lift reaches a 0.025-rad evidenced
ceiling during lift and gripper reaches 0.01 rad during lift, hold, and lower.
Strict uniform 0.05 rad remains report-only, Gate B is unchanged, and Gate C
is not authorized. Implementation commit `fbdb0aa` is confirmed on origin;
Reviewer 261 verifies this brief.
