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

## Pre-run boundary

Implementation commits `8da3cae` and `18f81e7` are remotely preserved. Signed
spec `522a1e5a...` binds the exact X checkpoint, all five recovery-dataset
files, the official 500-unique-index coverage order, unchanged X processor and
correction schedule, and ordered Gate B/Gate C/held-out stops. Central decision
`25e63103...` grants simulation training only. Runtime proof `04f2ce56...`
verifies the exact Python 3.12 stack, local MPS, both source trees, FFmpeg,
MuJoCo, Pillow, a signed one-frame MP4 smoke render, and 23,132,839,936 free
bytes against a 6-GiB minimum. Permit `68d9042d...` authorizes one attempt.
Thirty-two relevant tests and lint pass. Reviewer 239 authorizes that attempt;
no T20.36 attempt, checkpoint tensor read, model load, optimizer, rollout,
hardware, external compute, or Brev action has occurred.

## Result Boundary

The sole attempt completed 500 finite paired updates and emitted signed result
`02b543be...`, preserved at `3e1f2bd`. Its standard-objective ratio passes at
`0.0305642`, but all five decoded action chunks regress above the unchanged
0.05-rad gate, with maxima from `0.150601` to `0.187035` rad. Gate B is not
retained, so no closed-loop seed or mirror is reached. The one-use permit is
consumed and no retry is authorized. Reviewer 240 verifies the negative result
and routes only the optimizer-free Brief 192 evidence audit.
