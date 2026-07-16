# Brief 196 - T20.36e Exact ACT Control Pre-Run

## Objective

Implement, test, centrally compose, and remotely preserve the complete
T20.36e exact ACT Gate B diagnostic boundary before the sole local-MPS attempt.

## Frozen Input

- T20.36d spec `45c90dc05578546e589cbde28ac3f072e0a8b87c2dd1001f343a8d7f4d586a4b`.
- Exact local LeRobot source and T20.23 dataset/statistics identities already
  bound by that spec.
- Existing simulation-only training authority framework. No general training
  lock may substitute for a task-specific central decision.

## Required Implementation

1. A runner that validates the exact spec, source, dataset item, physical
   round trip, runtime dependencies, MPS availability, disk, and offline mode
   before creating the immutable attempt marker or importing model code.
2. Fresh compact ACT construction exactly as specified, with no cached model,
   pretrained backbone, network fallback, VAE, dropout, scheduler, retry, or
   sweep.
3. Exact loss, gradient, checkpoint-schedule, deterministic five-repeat action
   chunk, physical-error, stop, and result accounting with signed artifacts.
4. A one-use attempt marker that is created before model construction and
   binds spec, central decision, source commit, and seed.
5. A task-specific authority request/decision whose central composer can grant
   only this one local-MPS ACT control through the active run window. Missing,
   stale, contradictory, or broader evidence fails closed.

## Pre-Run Acceptance

- Positive and adversarial unit tests cover source/statistics drift, target
  substitution, coordinate error, model/config drift, schedule drift,
  duplicate attempts, incomplete checkpoints, non-finite evidence, false
  deterministic claims, gate tamper, and authority escalation.
- Dependency preflight runs without constructing a model or creating the
  attempt marker.
- The exact runner, request, central decision, preflight, tests, review, commit,
  and origin branch all agree before execution is eligible.

## Execution Boundary

Only after pre-run review and remote confirmation may the sole T20.36e attempt
create its marker, construct the fresh ACT, and execute the fixed schedule.
It must stop on the first passing post-baseline checkpoint or at 2,000 updates,
then sign and preserve the result whether positive or negative. No retry is
allowed.

## Prohibited Actions

Before pre-run preservation: no attempt marker, model construction/load,
inference, optimizer, or training. Throughout: no network/download, cached ACT
checkpoint, pretrained backbone, policy selection, SmolVLA entry, Gate B
amendment, Gate C, rollout, hardware, camera, serial, external compute, A100,
or Brev.

## Pre-Run Evidence

- Implementation commit `0f0caa7` is remotely preserved on the required
  branch. Thirty-five T20.36 regressions pass, including fail-closed source,
  gate, schedule, result, and authority cases.
- Model-free rehearsal found and corrected two runtime/API hazards before the
  one-use boundary: ACTConfig does not accept `dtype` or `compile_model`, and
  the ACT batch processor does not add a leading dimension to a horizon-50
  action tensor. Explicit single-item collation now yields action `(1,50,6)`,
  pad `(1,50)`, state `(1,6)`, and two image `(1,3,256,256)` tensors on MPS.
- Central decision `9c2a16d2...` grants only
  `simulation_training_ready`. Runtime preflight `d29b93e7...` rebinds the
  exact source/image/action/state hashes, Python 3.12, pinned dependencies,
  MPS, 20.12 GiB free, and remote source commit `0f0caa7` without constructing
  a model or creating the attempt marker.
- One-use permit `75f5e163...` authorizes only model construction, inference,
  and optimizer training for the frozen schedule after this complete pre-run
  boundary is remotely preserved. Retry, sweep, policy selection, SmolVLA,
  gate amendment, Gate C, rollout, hardware, external compute, and Brev remain
  false.

Reviewer Decision 245 verifies the pre-run boundary and opens exactly the sole
declared local-MPS attempt after its evidence commit is confirmed on origin.

## Execution Result

The sole attempt completed all 2,000 finite updates and signed negative result
`2ea2c246...`. The final supervised-objective ratio is `0.054918`, which passes
the unchanged 0.10 conjunct. All five deterministic decoded hashes match, and
their mean physical error is `0.0145525` rad, but the maximum physical error is
`0.442487` rad, so the unchanged 0.05-rad all-element conjunct fails. No retry
or Gate C is allowed. Reviewer Decision 246 verifies the negative result and
routes Brief 197 to an exact checkpoint-reload/per-joint localization boundary
before SmolVLA or any gate amendment.
