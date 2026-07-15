# Reviewer Decision 203 - Verify T20.35c Mixed Gate B Negative

**Decision:** `ACCEPT_T20_35C_MIXED_GATE_B_NEGATIVE`

## Reviewed Boundary

Brief 169, implementation `82614ec`, mixed-gate routing correction `0090856`,
result artifact commit `011e421`, attempt, complete run summary, trainable-only
checkpoint tree, signed result, tests, canonical state, and scoped diff were
reviewed together.

## Adversarial Findings

- Exactly one attempt marker `43b2b721...` exists and precedes model
  construction. No retry, continuation, second batch, or hyperparameter change
  occurred.
- The run completed exactly 500 finite objectives and 500 finite gradient
  norms at constant `2.5e-5` learning rate on the frozen T20.33 batch and seed
  schedule.
- The actual trainable boundary contains 693,422,112 elements across all 201
  Gemma-expert parameter names plus two tensors for each action in/out and real
  time-MLP projection. All 3,449,982,704 PaliGemma elements remain frozen; no
  PEFT or LoRA parameter exists.
- Checkpoint `439ae119...` binds a signed exact tensor manifest and the
  2,773,721,000-byte trainable-only safetensors file. The run verifier
  recomputes the checkpoint tree and tensor-name set.
- The objective gate passes honestly at ratio `0.004252`. The action gate fails
  honestly on all five seeds: mean error is `0.027275` to `0.036034` rad, but
  maximum error is `0.091908` to `0.150321` rad.
- All five mean and maximum errors improve materially over rank 16. This rejects
  both dead training and an unattainable objective-ratio explanation, while it
  does not establish Gate B, Gate C, closed-loop success, or policy acceptance.
- The initial result fallback named an objective-floor audit for every failure.
  Correction `0090856` was reviewed and remotely preserved before result
  signing; it routes this objective-pass/action-fail evidence to decoded-action
  residual localization.
- Hardware, cameras, serial devices, external compute, Brev, physical transfer,
  promotion, and destructive operations were not used.

## Disposition

Accept T20.35c as a verified mixed negative. Keep Gate B and every downstream
authority closed. T20.35d may open only as an optimizer-free deterministic
replay of the immutable expert-only checkpoint that reproduces all five action
hashes before localizing residuals by seed, timestep, and joint. Do not start
another training rung or Gate C work from this result.
