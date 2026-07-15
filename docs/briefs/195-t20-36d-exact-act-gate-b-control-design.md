# Brief 195 - T20.36d Exact ACT Gate B Control Design

## Objective

Design one deterministic, separately authorizable ACT one-batch memorization
control that distinguishes the shared data/normalization path from PI0.5's
flow-decoding path without selecting ACT as a product policy.

## Frozen Inputs

- T20.36c preflight `61fcf124...` and exact local LeRobot source identity.
- T20.33's canonical one-batch source observation and 50-step measured-action
  target, with the unchanged physical-radian Gate B maximum.
- T20.23's six-joint, two-camera, 256x256 dataset feature contract and
  train-only MEAN_STD statistics.
- The known local-MPS ACT source path. The cached third-party ACT checkpoint is
  not a valid initialization or processor substitute.

## Required Design

Emit one signed pre-run specification and deterministic verifier that bind:

1. the exact source observation, state/action joint order, two camera keys,
   50-step target, dataset statistics, and physical-action round trip;
2. a fresh ACT configuration with six state/action dimensions, exactly the two
   canonical cameras, one observation step, a 50-step chunk, fixed
   initialization seed, explicit no-download backbone initialization, and MPS;
3. one fixed repeated batch, optimizer/budget/learning-rate/clip values,
   immutable attempt marker, and no retry or sweep;
4. pre-update and declared checkpoints evaluated through deterministic ACT
   inference against the unchanged 0.05-rad physical maximum, with any
   objective-ratio metric reported using ACT's own fixed supervised objective
   and never substituted for physical action error; and
5. stop and routing rules: a pass supports shared-pipeline exoneration and a
   separately reviewed SmolVLA entry design; a fail routes shared
   data/normalization diagnosis. Neither outcome grants Gate C or policy
   acceptance.

## Acceptance

- The exact spec is derived mechanically from signed existing evidence.
- Missing/stale source, statistics, feature, target, seed, horizon, optimizer,
  gate, attempt, or authority fields fail closed.
- Deterministic positive and adversarial tests, lint, workflow audit,
  same-agent review, scoped commit, push, and remote confirmation agree.
- The output is design evidence only and cannot grant or execute the run.

## Prohibited Actions

No network, weight/checkpoint tensor read, pretrained checkpoint reuse, model
construction, inference, optimizer creation, training, attempt marker, ACT
run, SmolVLA entry, policy selection, Gate B amendment, Gate C, rollout,
hardware, camera, serial, external compute, A100, or Brev.

## Result Boundary

Signed spec `45c90dc0...`, preserved at implementation commit `b8b19cd`,
binds the exact canonical batch/statistics, fresh compact ACT, 2,000-update
ceiling, pre-registered evaluation schedule, deterministic repeats, unchanged
Gate B conjunction, one-use attempt contract, and diagnostic-only routes.
Reviewer 244 verifies Brief 195 and routes only the pre-run implementation and
task-specific central authority path in Brief 196. No attempt or execution
authority follows from the design artifact.
