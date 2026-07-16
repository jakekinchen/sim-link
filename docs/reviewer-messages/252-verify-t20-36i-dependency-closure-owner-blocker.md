# Reviewer Decision 252 - Verify T20.36i Dependency Closure And Owner Blocker

**Decision:** `VERIFY_DEPENDENCY_CLOSURE_BLOCK_REPLACEMENT_PENDING_OWNER`

## Reviewed Boundary

Brief 200; T20.36h result `3804eff6...`; pinned LeRobot head, pyproject, and
installed distribution metadata; consumed Python 3.12 environment; audit
`0804fd4f...`; implementation `9c08d21`; 59 T20.36 tests; exact verifier; and
the complete scoped diff.

## Adversarial Findings

- Pinned source and installed metadata agree on the `smolvla` root extra. Its
  local delegation graph resolves to `transformers-dep` and `accelerate-dep`.
- The exact closure has four distributions: LeRobot 0.6.1 and Transformers
  5.5.4 satisfy their requirements; `num2words>=0.5.14,<0.6.0` and
  `accelerate>=1.14.0,<2.0.0` are missing.
- The observed `num2words` error is therefore declared and predictable.
  Accelerate is an additional missing prerequisite the prior selected-version
  preflight would also have missed.
- Correction order is fail-closed: resolve the recursive extra, verify every
  installed version, sign the exact environment, and construct AutoProcessor
  offline before an attempt marker. Full policy construction remains after the
  marker and therefore counted.
- Audit `0804fd4f...` is model-free and records no installation, environment
  mutation, replacement readiness/authority, checkpoint access, inference, or
  optimizer work. Gate B remains unevaluated.

## Disposition

Verify T20.36i. Block T20.36j until the owner explicitly authorizes both the
bounded installation of the pinned SmolVLA extra closure into the existing
Python 3.12 venv and at most one replacement local-MPS attempt after the new
environment manifest and offline AutoProcessor smoke are verified on origin.
The unchanged Gate B and no-retry rule remain mandatory.

## Withheld Authority

No package installation, environment mutation, replacement attempt, model,
inference, optimizer, policy selection, Gate B change, Gate C, rollout,
hardware, external compute, or Brev.
