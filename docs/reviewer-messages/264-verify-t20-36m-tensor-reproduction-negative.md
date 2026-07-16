# Reviewer Decision 264 - Verify T20.36m Tensor Reproduction Negative

**Decision:** `VERIFY_SMOLVLA_NEGATIVE_ROUTE_T20_35X_COMPARISON`

## Reviewed Boundary

Brief 206; owner grant `155a7338...`; central decision `31eabbbd...`;
one-use permit `374ad4f2...`; attempt `c69d3904...`; tensor artifact
`45a3369d...`; run `0b7c98b6...`; result `4f101f38...`; result commit
`a5e7c6adf7f2c51b6708640a419a1c14989da6bf`; exact T20.36j and T20.36m
verifiers; focused and dependency tests; branch/remote parity; and the complete
scoped diff.

## Findings

- All five existing T20.36j action hashes reproduce exactly and both repeats
  are bit-identical for every registered inference seed.
- The tensor artifact is directly bound by the tracked result. The result also
  retains every seed's hash, maximum absolute error, maximum threshold ratio,
  pass state, and violation count.
- The final-to-baseline objective ratio is `0.022866`, but every seed fails the
  frozen amended Gate B. Violation counts are 40, 25, 52, 27, and 18, totaling
  162; maximum threshold ratios are `7.0363`, `7.3632`, `9.1991`, `10.6410`,
  and `5.0790`.
- The post-run evidence-binding correction only recomposed the deterministic
  tracked result from the already-signed run; it did not reconstruct the model,
  rerun inference, change a score, or change a gate.
- One historical T20.36j-A cache-audit test now observes the installed
  environment and reports no pending package changes. That pre-install-state
  expectation is already documented as superseded; the exact T20.36j source
  verifier and all current T20.36m tests pass.
- No optimizer, training, new seed, extra repeat, threshold change, Gate C,
  policy selection, hardware, network, external compute, or Brev action ran.

## Disposition

Verify T20.36m negative for SmolVLA; no SmolVLA retry or Gate C route is
available. Retained T20.35x still requires the owner-directed amended-gate
comparison. Because its signed artifacts contain only hashes and aggregates,
route to a fresh hash-bound reproduction under Brief 207 before any global
branch disposition.

## Withheld Authority

No model retry, inference, optimizer/training, gate change, Gate C execution,
policy selection/promotion, hardware, network, external compute, or Brev.
