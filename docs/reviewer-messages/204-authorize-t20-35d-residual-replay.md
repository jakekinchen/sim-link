# Reviewer Decision 204 - Authorize One T20.35d Residual Replay

**Decision:** `CONTINUE_ONE_T20_35D_EXACT_REPLAY`

## Reviewed Boundary

Brief 170, implementation `7162497`, spec `b083c593...`, narrowed permit
`bd3b0933...`, immutable T20.35c result/run/checkpoint identities, runner,
tests, canonical state, and scoped diff were reviewed after remote
preservation.

## Adversarial Findings

- The evaluation spec binds the exact T20.35c source spec, result, run,
  attempt, checkpoint tree, trainable-name identity, dataset target hash, five
  inference seeds, and five expected decoded hashes and metrics.
- The narrowed permit inherits the still-active central decision but authorizes
  only `simulation_model_load` and `simulation_model_inference`. It explicitly
  denies optimizer training, checkpoint mutation, closed-loop rollout,
  hardware, external compute, Brev, transfer, and promotion.
- Before consuming the one replay attempt, the runner streams and verifies the
  complete checkpoint tree. After the marker, it verifies every safetensors
  key, shape, dtype, element count, and finite value before loading the exact
  expert-only boundary.
- The runner contains no optimizer construction. It decodes exactly one
  horizon-50 chunk for each frozen inference seed and fails closed before
  interpretation if any prior chunk hash or metric does not reproduce.
- The signed report retains all five full decoded matrices, the target matrix,
  absolute residual matrices, every threshold-exceedance coordinate, and
  deterministic joint/timestep concentration summaries.
- Classification thresholds are predeclared: at least 50% of exceedances on
  one joint is joint concentration; at least 60% in the first/last five
  timesteps is boundary concentration. Combined and distributed cases remain
  distinct.
- Existing user-owned config changes and external checkouts are excluded.

## Disposition

After this decision is committed, pushed, and confirmed on
`origin/codex/pi05-autolearn-loop`, execute exactly one local-MPS replay. Do not
retry if the checkpoint, model, inference, hash, or report step fails. Adjudicate
only the predeclared residual localization; do not train or enter Gate C.
