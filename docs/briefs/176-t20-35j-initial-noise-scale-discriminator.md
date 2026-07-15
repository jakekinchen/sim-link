# Brief 176 - T20.35j Initial-Noise Scale Discriminator

## Objective

Test whether T20.35i's distributed seed variance is caused by the standard
normal initialization amplitude used by the pinned PI0.5 flow sampler. Change
only initial-noise scale in one inference-only evaluation.

## Frozen Sources And Factor

- T20.35i report `ac87de7b21c7698fe5b02d1e57b06cab009bc6a92257bbcc52c27111cc04a6f0`.
- T20.35g corrected spec/result, expert-only checkpoint, exact batch/target,
  processors, 10 denoising steps, five inference seeds, and baseline hashes.
- Pinned LeRobot stack and exact runtime `modeling_pi05.py` source hash.
- Initial-noise scales, in evaluation order: `1.0`, `0.5`, `0.0`.
- Maximum decoded action error: `0.05` rad.

For every scale/seed pair, reset the same torch seed, sample the standard
normal tensor through the pinned `sample_noise`, multiply only that tensor by
the declared scale, and pass it to the unchanged sampler. No other factor may
change. Scale 1.0 must reproduce all five T20.35g hashes before candidates are
interpreted.

## Metrics And Routing

For each scale record five decoded chunks/hashes, per-seed max/mean errors,
worst-seed maximum, aggregate mean, and aggregate raw five-seed spread.

- Gate B action pass requires all five chunks at or below `0.05` rad. Prefer
  the largest passing candidate scale, preserving the closest default.
- Without a pass, a candidate is directionally positive only if worst-seed
  maximum, aggregate mean, and aggregate raw spread are all strictly below
  scale 1.0. Select the positive candidate by lowest worst error, then mean,
  then largest scale.
- A passing candidate routes only a separately reviewed Gate C reproduction.
- A positive non-pass routes sampler/noise-distribution audit with Gate B closed.
- Rejection routes model robustness correction with Gate B closed.

## One-Use Runtime Boundary

The implementation must write a signed attempt marker after branch/authority/
source/checkpoint-tree checks and before model/checkpoint tensor access. A
separate same-agent pre-run decision, scoped commit, push, and remote
confirmation must authorize exactly one Python 3.12 local-MPS model-load and
inference attempt. Existing attempt/result files fail closed.

## Prohibited Actions

- Optimizer creation, training, continuation, or statistics changes.
- Checkpoint/dataset/source mutation or hidden postprocessing correction.
- Cadence changes, additional scales/seeds, or retries.
- Closed-loop rollout, Gate C execution, policy acceptance, promotion,
  hardware, camera, serial, external compute, or Brev.

## Acceptance

- Tests cover lineage/source drift, scale/order/seed drift, identical base
  noise, baseline hashes, metrics, spread, selection and routes, non-finite
  values, one-use permit/attempt, and every forbidden truth flag.
- Spec, permit, runner, focused/relevant tests, pointer check, workflow audit,
  and fresh same-agent adversarial review are remotely preserved before the
  sole runtime attempt.

## Pre-Run Boundary

Implementation `ed05689`, spec `a3dc0acb...`, permit `545a71c6...`, and
Reviewer 213 authorize one Python 3.12 local-MPS model-load/inference attempt
after remote preservation. The runner records the same base-noise hash for each
seed across all scales and requires exact scale-1 action hashes. Five focused
and 86 relevant tests pass; spec/permit verification agrees under Python 3.11
and 3.12. No model, checkpoint tensor, inference, optimizer, mutation, rollout,
Gate C, hardware, external compute, or Brev action occurred at this boundary.
