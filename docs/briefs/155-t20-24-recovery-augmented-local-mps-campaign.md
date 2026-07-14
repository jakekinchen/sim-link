# Slice Brief 155 - T20.24 Recovery-Augmented Local-MPS Campaign

**Date:** 2026-07-14

## Objective

Run the exact centrally authorized T20.23 recovery-augmented PI0.5 campaign for
500 local-MPS optimizer updates, then evaluate its frozen adapter unassisted on
held-out source seeds 6 and 7 under strict-v2 semantics.

## Contract

- Reverify the T20.23 dataset, training specification, clean model snapshot,
  owner grant, and active central `simulation_training_ready` decision before
  creating the run directory or loading the model.
- Invoke the official package training entrypoint from the clean
  content-addressed `lerobot/pi05_base` snapshot with the exact T20.23 dataset,
  package quantile statistics, rank-4 LoRA, batch size one, local MPS, fixed
  seed 20260714, offline mode, and exactly 500 optimizer updates.
- Record every finite loss, exact argv/environment, checkpoint tree, dataset /
  specification / authority identities, and zero external/Brev/physical use.
- Freeze the final adapter before evaluation. Evaluate seeds 6 and 7
  independently with action horizon 5, fixed inference seeds, no projection,
  no active assistance, no source-action fallback, and no checkpoint mutation.
- Grade each complete 244-frame rollout under strict-v2. Record any success or
  failure truthfully. This slice may expose a local candidate capability but may
  not grant `simulation_policy_accepted`, physical transfer, or promotion.
- Do not access hardware or cameras, instantiate a physical robot, start
  external compute or Brev, change the twin, or consume Robo Scan evidence.

## Acceptance Criteria

- Tests first prove exact campaign argv/update accounting, finite-loss and
  checkpoint gates, two-seed coverage, distinct source binding, no projected or
  assisted frames, honest positive/negative result composition, signed mutation
  rejection, and authority/execution-field containment.
- The official trainer completes exactly 500 finite updates and emits a
  content-addressed reloadable adapter bound to the clean base and T20.23
  processor/statistics identities.
- Seeds 6 and 7 each run exactly once through the frozen adapter, retain their
  source identities, and produce full strict-v2 stage evidence plus rendered
  keyframes.
- A signed result gate records per-seed outcomes and aggregate strict-success
  count without changing accepted-policy, transfer, or promotion pointers.
- Focused tests, relevant regressions, same-agent adversarial review, canonical
  state, ledger, MVP plan, session log, reviewer decision, scoped commits, and
  remote branch agree before T20.24 is described as verified.

## Out Of Scope

Additional optimizer rungs; model/hyperparameter sweeps; failure imitation;
reward weighting or RL; ensemble execution; policy promotion; physical canary;
hardware/camera access; twin calibration; Robo Scan; external compute; or Brev.
