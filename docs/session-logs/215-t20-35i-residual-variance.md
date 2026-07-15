# Session Log 215 - T20.35i Residual Variance

## Evidence

- Implementation: `aa15de85ed6c35b888f43db29cc665c17ed6ff0e`.
- Report identity:
  `ac87de7b21c7698fe5b02d1e57b06cab009bc6a92257bbcc52c27111cc04a6f0`.
- Report file SHA-256:
  `f65c5e97265ca5dd0f3ab9d7b48a391652c4eb7b06d188bd10fef8752f26a48e`.
- Five focused and 81 relevant tests pass.
- Exact verification passes under Python 3.11 and 3.12.

## Result

- Remaining exceedances: 96 across all five seeds and four channels.
- Top-two seeds: 56.25%; top-two channels: 67.71%; boundaries: 31.25%.
- Unique failure positions: 76.
- Maximum raw decoded spread: `0.183018` rad.
- Classification: `distributed_seed_channel_variance`.

Reviewer 212 routes T20.35j to one inference-only initial-noise-scale
discriminator. Gate B and Gate C remain closed. No model, checkpoint,
inference, optimizer, mutation, hardware, external compute, or Brev action
occurred.
