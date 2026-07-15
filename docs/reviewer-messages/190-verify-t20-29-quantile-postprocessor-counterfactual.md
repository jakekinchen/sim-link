# Reviewer Decision 190 - Verify T20.29 Quantile-Postprocessor Counterfactual

`ACCEPT_VERIFIED_POSTPROCESSOR_ACCOUNTING_ONLY`

Reviewed Brief 160 through implementation commit `7473272`, artifact commit
`5fed879`, and counterfactual identity
`59474892f9d2da8605cff6429681b432cc8619be2e3a6c36fbe514b763ee0e9e`.

Both pinned checkpoint postprocessors declare `ACTION: QUANTILES`, and their
stored q01/q99 tensors match the bound clean and recovery dataset statistics at
float32 precision. The package formula source, config/state files, statistics,
T20.26 batches, T20.27 gate, exact source action, coordinate transform, and five
paired inference seeds are independently bound and fail closed on substitution.

Holding clean normalized outputs fixed and decoding them with recovery action
quantiles raises mean source-action error from 0.50833 to 0.62134 rad, a
0.11301 rad shift. T20.27 observed a 0.11094 rad recovery-minus-clean
regression, leaving a -0.00208 rad residual within the declared 0.01 rad
accounting tolerance. The reverse swap lowers recovery-output error by 0.11370
rad. Own-stat round trips and cross-stat coordinate clipping are within 1e-8.

Same-agent adversarial review covered stale or substituted stats, config/state
hashes, formula source, candidate/seed/joint coverage, malformed and non-finite
quantiles/actions, zero spans, signed mutation, coordinate clipping, authority
escalation, nondeterminism, path aliasing, and cleanup. One hundred one relevant
tests pass after hardening the independent-evidence verifier, and the artifact
reconstructs exactly from live pinned sources.

This accepts only a postprocessor-level counterfactual. It does not isolate the
full training effect or authorize model inference, optimizer training, action
application, rollout, policy acceptance, transfer, promotion, hardware,
external compute, or Brev. Nominal-action-quantile freezing is selected only as
the next separately reviewed recovery-training ablation.
