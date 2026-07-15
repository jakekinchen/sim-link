# Reviewer Decision 227 - Authorize T20.35r Full-Path Correction

**Decision:** `AUTHORIZE_ONE_T20_35R_FULL_PATH_TRAINING_EVALUATION_ATTEMPT`

## Reviewed Boundary

Brief 184, implementation commits `bac3877` and `ef90668`, spec
`70be21a2...`, central authority `f4ef827b...`, T20.35p checkpoint/result,
T20.35q paths/result, runner, tests, canonical state, and the complete scoped
diff were reviewed before T20.35r model loading or optimizer creation.

## Adversarial Findings

- The source is exactly T20.35p checkpoint `9358cee4...`; its 2-file tree is
  frozen and rechecked before and after the attempt.
- All 50 T20.35q self-generated pre-update states are bound by seed, step,
  time, and hash. PI0.5 reconstruction errors are at most `4.45e-16` for state
  and `1.12e-15` for target velocity.
- The schedule contains exactly 500 updates and uses each of 50 examples
  exactly 10 times. Learning rate, optimizer settings, expert-only parameter
  boundary, RNG seed, processors, target, sampler, and five evaluation seeds
  are frozen.
- Gate B still requires the final standard-objective ratio at most 0.10 and
  every decoded chunk at most 0.05 rad. Correction-set improvement alone
  cannot pass Gate B or open Gate C.
- The immutable attempt marker precedes LeRobot activation, checkpoint tensor
  access, model construction, inference, and optimizer creation. An existing
  run root fails closed, so retry is impossible.
- The central composer grants only `simulation_training_ready`. Physical
  transfer, promotion, hardware, external compute, and Brev remain denied.
- Fifty-seven relevant Python 3.12 tests pass; exact spec, authority, and
  model-free preflight verify after remote preservation.

## Disposition

Authorize exactly one Python 3.12 local-MPS T20.35r training/evaluation
attempt under authority `f4ef827b...`. Interpret only its signed run and result.
Do not retry, change a factor, enter Gate C, access hardware, or start external
compute.
