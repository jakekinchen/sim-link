# Reviewer Decision 212 - Verify T20.35i Residual Variance

**Decision:** `VERIFY_DISTRIBUTED_VARIANCE_AND_ROUTE_INITIAL_NOISE_SCALE`

## Reviewed Boundary

Brief 175, implementation/report commit `aa15de8`, report `ac87de7b...`, exact
T20.35g/h sources, writer/verifier, tests, canonical state, and the complete
scoped diff were reviewed after model-free construction.

## Adversarial Findings

- Every corrected hash reproduces and every element satisfies the exact
  `5/4 * (raw seed - five-seed mean)` identity within `1e-15`.
- All five seeds contain failures. The largest seed has 27/96 (28.125%); the
  top two seeds have 54/96 (56.25%), below the 50%/75% gates.
- Wrist roll has 37/96 (38.54%); wrist roll plus shoulder lift have 65/96
  (67.71%), below the 50%/75% channel gates.
- First/last-five boundaries have 30/96 (31.25%), below the 60% gate.
- Seventy-six unique timestep/channel positions fail. Raw five-seed decoded
  spread reaches `0.183018` rad and averages `0.091598` across failure
  positions. The residual is not a boundary-, seed-, or channel-only fault.
- The report keeps Gate B, correction selection, model/inference, optimizer,
  rollout, hardware, external compute, Brev, and promotion claims false.
- Five focused and 81 relevant tests pass; exact verification passes in both
  configured Python runtimes.

## Disposition

Accept `distributed_seed_channel_variance`. Route T20.35j to exactly one
separately reviewed inference-only initial-noise-scale discriminator against
the same 10-step baseline, checkpoint, target, and five seeds. Do not add an
optimizer, enter Gate C, or broaden any authority.
