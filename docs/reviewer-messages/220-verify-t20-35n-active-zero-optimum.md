# Reviewer Decision 220 - Verify T20.35n Active-Zero Optimum

**Decision:** `VERIFY_ACTIVE_ZERO_ENDPOINT_ROUTE_FLOW_CONSISTENCY`

## Reviewed Boundary

Brief 180, implementation/spec/permit, consumed attempt `c8eecd80...`, signed
result `d3e6e5d9...`, result commit `4e37e19`, verifier, tests, canonical state,
and the complete scoped diff were reviewed after the sole authorized attempt.

## Adversarial Findings

- Active-scale endpoints 0/1 remain exact and every interior call uses the
  signed base-noise tensor with all padded dimensions fixed at scale 1.
- Worst error rises monotonically `0.066398`, `0.082665`, `0.102040`,
  `0.150321` at active scales 0, 0.25, 0.5, 1.
- Aggregate mean and cross-seed spread also rise monotonically. Neither
  interior scale passes or improves the active-zero endpoint.
- Active-zero remains off the default prior and is not relabeled as an accepted
  sampler. Its `0.066398` worst error still fails the 0.05-rad gate.
- The one-use permit is consumed. No retry, optimizer, training, mutation,
  correction, rollout, Gate C, hardware, external compute, or Brev action
  occurred.

## Disposition

Reject further active-scale refinement. Open T20.35o under Brief 181 to
instrument the exact active-zero/padded-normal learned velocity path against
the deterministic single-target straight-flow reference. Gate B and Gate C
remain closed.
