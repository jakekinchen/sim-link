# Reviewer Decision 245 - Verify T20.36e Exact ACT Control Pre-Run

**Decision:** `VERIFY_PRE_RUN_OPEN_ONE_EXACT_ACT_CONTROL_ATTEMPT_AFTER_REMOTE`

## Reviewed Boundary

Brief 196; spec `45c90dc0...`; implementation commit `0f0caa7`; complete
runner, artifact, preflight, and authority diffs; signed central decision
`9c2a16d2...`; runtime preflight `d29b93e7...`; permit `75f5e163...`; focused
and broad regression output; model-free ACT configuration/processor rehearsal;
and the current branch/remote state.

## Adversarial Findings

- The central composer grants only `simulation_training_ready`. The owner
  grant and one-use permit restrict execution to construction, inference, and
  optimizer training for one local simulation attempt through 23:27 CDT.
- Runtime preflight rebinds remote commit `0f0caa7`, Python 3.12, the exact six
  dependency versions, MPS, 20.12 GiB free, episode/frame/task, both image
  tensor hashes, the physical action/state hashes, and coordinate errors below
  `7.11e-8` rad. It imports no ACT model and reads no checkpoint tensor.
- Rehearsal caught two concrete API hazards before the one-use marker: removed
  unsupported ACTConfig `dtype`/`compile_model` arguments and added explicit
  single-item collation because the processor does not batch a horizon action.
  Processed shapes are action `(1,50,6)`, pad `(1,50)`, state `(1,6)`, and two
  image `(1,3,256,256)` tensors on MPS.
- The attempt marker must exist before ACT model import/construction. Current
  run, attempt, checkpoint, and result paths are absent. The runner rejects a
  non-origin HEAD or a permit source that is not its ancestor.
- Objective and gradient traces reject non-finite values. Evaluation order is
  a strict prefix of 0/100/250/500/1,000/2,000, stops at first pass, and requires
  the full ceiling on failure. Five decoded hashes must agree for a pass.
- Result claims remain diagnostic. Pass cannot select ACT, repair PI0.5 by
  claim, change Gate B, or open Gate C; fail cannot by itself prove dataset
  fault. Thirty-five T20.36 regressions and workflow/diff checks pass.

## Disposition

Verify the complete pre-run boundary. After this decision and its five signed
artifacts are committed, pushed, and confirmed on
`origin/codex/pi05-autolearn-loop`, execute exactly one T20.36e attempt. Stop at
the first passing checkpoint or update 2,000, preserve the result whether
positive or negative, and do not retry.

## Withheld Authority

No network/download, cached ACT checkpoint, second attempt, retry, sweep,
policy selection, SmolVLA entry, Gate B amendment, Gate C, closed-loop rollout,
policy acceptance, hardware, camera, serial, external compute, or Brev.
