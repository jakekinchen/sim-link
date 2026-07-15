# Reviewer Decision 223 - Authorize T20.35p Terminal Flow Correction

**Decision:** `AUTHORIZE_ONE_T20_35P_TERMINAL_FLOW_TRAINING_EVALUATION`

## Reviewed Boundary

Brief 182, implementation `7ee3803`, spec `fd4f75f6...`, central authority
decision `c69090da...`, T20.35c checkpoint/result, T20.35o trajectory result,
runner, tests, canonical state, and the complete scoped diff were reviewed
before model or checkpoint tensor access.

## Adversarial Findings

- The correction set contains exactly 15 examples: five signed seeds times
  steps 7, 8, and 9. State and target-velocity reconstruction errors are at
  most `1.12e-16` and `1.12e-15`, below the `2e-12` contract.
- Each example is used exactly 30 times in seed-major order for 450 updates.
  AdamW, `2.5e-5` learning rate, betas, epsilon, zero weight decay, unit
  gradient clipping, and RNG seed are explicit.
- The exact expert-only checkpoint tree and complete 693,422,112-parameter
  trainable boundary are inherited. PaliGemma stays frozen and PEFT remains
  absent.
- The runner must reproduce the loaded source checkpoint's standard objective
  before training. After training, Gate B uses the original `0.959079` baseline
  and 0.10 ratio gate, not merely the targeted correction loss, so catastrophic
  forgetting cannot pass.
- Evaluation freezes active noise at zero, padded noise normal, the five exact
  base-noise hashes, 10 steps, target/processors, and the 0.05-rad all-seed
  action gate.
- The immutable attempt marker precedes stack/model import, checkpoint tensor
  access, and optimizer creation. Existing output fails closed; no retry path
  exists.
- Central composition grants only `simulation_training_ready`. Thirty-six
  relevant tests pass under Python 3.12, the six new tests pass under Python
  3.11, and spec, authority, and model-free runner preflight verify exactly.
  No rollout, Gate C, hardware, external compute, or Brev path exists.

## Disposition

After remote preservation, authorize exactly one Python 3.12 local-MPS
training/evaluation attempt under decision `c69090da...`. Interpret only its
signed run and result. Do not retry, add states/seeds/updates, enter Gate C, or
mutate any source.
