# Reviewer Decision 230 - Authorize T20.35t Balanced Correction

**Decision:** `AUTHORIZE_ONE_T20_35T_TIME_NORMALIZED_STANDARD_REPLAY_ATTEMPT`

## Reviewed Boundary

Brief 186, implementation `545a563`, spec `34881e21...`, central authority
`8387945b...`, T20.35p checkpoint, T20.35q paths, T20.35s audit, runner,
tests, canonical state, and the complete scoped diff were reviewed before
T20.35t model loading or optimizer creation.

## Adversarial Findings

- The source is the exact pre-regression T20.35p checkpoint `9358cee4...`; its
  two-file tree is verified before and after the attempt.
- All 50 path examples reconstruct exactly. Per-step weights are derived only
  from signed T20.35s baseline means and range from `19.6296` to `0.128891`,
  making all 10 initial weighted step means equal to `0.120801`.
- Exactly 500 optimizer steps are allowed. Every correction example is used
  10 times, and each update accumulates one weighted correction gradient plus
  one coefficient-1.0 standard replay gradient under a unique frozen seed.
- The signed run records raw, weighted, standard, and joint objectives for
  every update. The verifier recomputes weight application, joint sums,
  per-example weighted evidence, schedules, seeds, and source-tree stability.
- Gate B still requires the original standard-objective ratio at most 0.10
  and every decoded chunk at most 0.05 rad. Neither raw nor weighted
  correction improvement can open Gate C.
- The attempt marker precedes LeRobot activation, checkpoint access, model
  construction, inference, and optimizer creation. Existing output fails
  closed, preventing retry.
- Central authority grants only `simulation_training_ready`; physical
  transfer, promotion, hardware, external compute, and Brev remain denied.
- Fifty-four relevant Python 3.12 tests and exact spec, authority, and
  model-free preflight pass after remote preservation.

## Disposition

Authorize exactly one Python 3.12 local-MPS T20.35t training/evaluation
attempt under authority `8387945b...`. Interpret only its signed run and
result. Do not retry, change a weight/seed/factor, enter Gate C, access
hardware, or start external compute.
