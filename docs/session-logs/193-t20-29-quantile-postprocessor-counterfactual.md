# Session Log 193 - T20.29 Quantile-Postprocessor Counterfactual

## Scope

Brief 160 cross-decoded five already captured paired frame-zero outputs under
the pinned clean and recovery action quantiles. No model inference, rollout,
action application, optimizer, hardware, camera, external compute, or Brev was
used.

## Evidence

- Counterfactual identity:
  `59474892f9d2da8605cff6429681b432cc8619be2e3a6c36fbe514b763ee0e9e`.
- Observed T20.27 recovery-minus-clean MAE: 0.11093614 rad.
- Clean outputs under recovery quantiles: +0.11301232 rad MAE.
- Accounting residual: -0.00207618 rad against a 0.01 rad tolerance.
- Recovery outputs under clean quantiles: -0.11369938 rad MAE.
- Paired seed count: five.
- Own-stat round trip and cross-stat coordinate clipping: at most 1e-8.

## Result And Validation

Recovery action-quantile shift accounts for the observed paired frame-zero
regression within tolerance in this postprocessor-only counterfactual. It does
not isolate full training causality. The next bounded hypothesis is a separate
nominal-action-quantile-freezing recovery ablation; no optimizer was opened.

One hundred one relevant tests passed. Same-agent review hardened the verifier
to require independently supplied source hashes and covered substitution,
non-finite values, zero spans, seed/joint coverage, clipping, signed mutation,
authority, determinism, path aliasing, and cleanup.
