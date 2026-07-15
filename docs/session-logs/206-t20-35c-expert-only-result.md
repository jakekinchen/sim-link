# Session Log 206 - T20.35c Expert-Only Result

## Scope

Execute and adjudicate the sole Brief 169 local-MPS expert-only capacity run.

## Evidence

- Attempt: `43b2b7211dd3700e5a8686a10d57f27fe74525b4d4614c8e74993142be57c939`.
- Run: `9b1af8ee0020fef65b3990b587268642c4eb1e137f8b252729e79d0d5a5ad650`.
- Checkpoint: `439ae119842fe5f9639b3e3e9b76f029678fd4b4257dfd6308253f6d2832c29f`.
- Result: `f6f6b024c169ffec9c59be9e8a111e756aae2b70729ae30ad016b29ee402df47`.
- 500/500 objective values and 500/500 pre-clip gradient norms are finite.
- 693,422,112 parameters are trainable; 3,449,982,704 PaliGemma parameters are
  frozen and zero PaliGemma parameters are trainable.
- Baseline objective is `0.959079`; final five-seed objective is `0.004078`, a
  ratio of `0.004252`, passing the `0.10` objective gate.
- Five decoded mean errors are `0.027275` to `0.036034` rad. Maximum errors are
  `0.091908` to `0.150321` rad, so every seed misses the `0.05` action gate.
- Compared with rank 16, mean-error improvement is `0.114039` to `0.220788`
  rad and maximum-error improvement is `0.594313` to `1.317674` rad.

## Validation

- The immutable attempt, signed run, 2.77 GB checkpoint tree, safetensors key
  set, and result all verify exactly.
- Thirty-six focused T20.33-T20.35c tests pass after the mixed-gate routing
  correction; the signed result recomposes exactly.
- No retry, continuation, second optimizer, Gate C work, closed-loop rollout,
  hardware, external compute, Brev, transfer, promotion, or policy acceptance
  occurred.

Gate B remains failed only on the decoded maximum-error criterion. Reviewer 203
routes T20.35d to optimizer-free exact replay and residual localization.
