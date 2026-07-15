# Reviewer Decision 242 - Verify T20.36b Gate B Retention Contract

**Decision:** `VERIFY_RETENTION_CONTRACT_ONLY_SOURCE_PASSES_ROUTE_LOCAL_POLICY_PREFLIGHT`

## Reviewed Boundary

Brief 193; X, T20.36, and T20.36a signed inputs; generic evidence/spec/decision
builders; historical fixture; adversarial tests; spec `6e56f6ff...`; decision
`e709c30c...`; implementation commit `5fdc36c`; and the complete scoped diff.

## Adversarial Findings

- The contract uses exactly the unchanged 0.10 standard ratio and five fixed
  0.05-rad physical maxima. Proxy metrics are report-only.
- X passes both conjuncts and is labelled rollback capability. T20.36 passes
  only the standard ratio, fails all five action rows, and is rejected. No
  coverage candidate is selected.
- The historical fixture explicitly records that it is not a pre-registered
  campaign schedule. A future non-fixture spec requires a registration-boundary
  identity and remote preservation before optimizer creation.
- Positive and no-pass routes are deterministic. Missing/reordered seeds,
  duplicate or unordered checkpoints, changed thresholds, stale identities,
  non-finite values, proxy-only claims, decision tamper, and authority
  escalation fail closed.
- Twenty-five relevant tests pass; exact regeneration, lint, compile, and
  workflow checks pass.
- The contract grants no checkpoint read, model, inference, optimizer,
  campaign, Gate C, policy acceptance, hardware, external compute, or Brev.

## Disposition

Verify T20.36b. With no post-source π0.5 candidate, open Brief 194 for a
read-only local ACT/SmolVLA source/cache/dataset compatibility preflight. It
may route a later owner decision but cannot select or run a policy track.
