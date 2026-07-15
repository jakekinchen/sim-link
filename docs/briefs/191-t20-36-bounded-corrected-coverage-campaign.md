# Brief 191 - T20.36 Bounded Corrected-Coverage Campaign

## Objective

Turn the verified T20.35x one-batch capability into one bounded full-coverage
candidate, then test capability gates in order: Gate B retention, one
training-seed strict-v2 closed-loop reproduction, and only then held-out seeds
6 and 7.

## Frozen Sources

- Exact T20.35x checkpoint `40c94f66...` and Gate B result `e79dacff...`.
- Exact T20.23 recovery-augmented dataset manifest `f12c95a3...`, training spec
  `5ad2f407...`, ten episodes, and 2,330 frames. No dataset or statistics
  change is permitted.
- T20.35x physical joint weights, time weights, 50 correction examples,
  processors, sampler identity, and unchanged Gate B thresholds.

## Campaign Contract

Implement and test one deterministic 500-update expert-only local-MPS
campaign. Each update pairs one frozen recovery-dataset standard gradient with
one balanced T20.35x time-and-joint-weighted correction replay gradient before
the step. Freeze the optimizer, learning rate, sample order, replay order,
seeds, checkpoint source, and one-attempt semantics in a signed spec. Record
both objectives separately so replay cannot conceal dataset regression.

## Evaluation Order

1. Re-run unchanged Gate B on the exact fixed batch. If it fails, stop before
   closed-loop execution.
2. If Gate B is retained, run one unassisted policy-owned training-seed
   strict-v2 reproduction with a complete signed trace and mirror MP4.
3. Only if that Gate C reproduction passes, evaluate frozen held-out seeds 6
   and 7 in order, each with a signed trace and mirror MP4.

No held-out result may compensate for a failed lower gate. Scripted,
controller-assisted, projected, or replayed completion is not policy success.

## One-Use Boundary

Implementation, deterministic tests, signed spec, task-specific central
authority, dependency-complete runtime proof, immutable permit, same-agent
adversarial review, scoped commits, push, and remote confirmation must precede
checkpoint tensor access, model construction, optimizer creation, or rollout.

## Prohibited Actions

No second rung, retry, dataset/statistics mutation, changed Gate B threshold,
concurrent campaign, hardware, camera, serial, physical transfer, promotion,
external compute, or Brev.

## Acceptance

One signed result records all 500 finite paired updates, Gate B retention, the
ordered strict-v2 evaluation actually reached, complete traces, and content-
addressed mirrors. It may route Gate C diagnosis or the next capability gate;
it cannot itself grant physical readiness or promotion.
