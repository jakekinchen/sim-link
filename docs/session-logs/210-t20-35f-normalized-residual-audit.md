# Session Log 210 - T20.35f Normalized Residual Audit

## Scope

Audit the retained wrist-roll and gripper residuals in the exact PI0.5 action
normalization space and distinguish systematic bias from seed variance without
model or checkpoint access.

## Evidence

- Signed audit:
  `85c24c5cd9a08c1a8153361bbdebaab0cedde28c5c1ec1a79bd1544924354432`.
- T20.17 action-statistics file:
  `9c013fde21c80e2dd0d184ac3122f1ce4fd75e662dedef97fd5f6b651376cf4c`.
- Action normalization: QUANTILES, q01/q99, no normalized-value clipping.
- Wrist roll: 164 reproduced exceedances; 39/50 targets outside the quantile
  range; zero bound hits; 84.81% systematic-bias share.
- Gripper: 121 reproduced exceedances; 32/50 targets outside the quantile
  range; zero bound hits; 82.33% systematic-bias share.
- Selected route: `gate_b_inference_denoising_cadence_discriminator` against
  the pinned 10-step default.

## Validation

- Three focused and 84 relevant tests passed; the audit writer verifies exactly.
- Source hashes, lineage identities, physical/normalized gate equivalence,
  decomposition closure, route, and all no-authority flags verify.
- No model, inference, optimizer, checkpoint read or mutation, dataset write,
  Gate C, rollout, hardware, external compute, or Brev occurred.

Reviewer 207 accepts T20.35f and routes T20.35g as the next inference-only
discriminator, subject to its own pre-run review boundary.
