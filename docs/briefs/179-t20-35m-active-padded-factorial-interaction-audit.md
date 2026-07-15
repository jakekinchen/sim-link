# Brief 179 - T20.35m Active/Padded Factorial Interaction Audit

## Objective

Quantify the 2x2 active-noise and padded-noise effects in T20.35l before
choosing another inference factor. This slice is deterministic and model-free.

## Frozen Source

Bind signed T20.35l result `b4fc6060...` and its four conditions in order:
all-normal, active-normal/padded-zero, active-zero/padded-normal, and all-zero.
Recompute each condition's chunks, hashes, metrics, and Gate B status through
the T20.35l verifier before calculating any contrast.

## Required Contrasts

For worst-seed maximum error, aggregate mean error, and raw cross-seed spread,
compute:

- active-noise effect with padded noise zero;
- active-noise effect with padded noise normal;
- padded-noise effect with active noise zero;
- padded-noise effect with active noise normal;
- interaction: all-normal minus active-normal/padded-zero minus
  active-zero/padded-normal plus all-zero.

Positive effects mean the named noise increases error. Preserve signs; do not
take absolute values or average away context.

## Routing

If active noise is harmful at both padded settings across all three metrics and
the best condition keeps padded noise normal, route one separately reviewed
near-zero active-noise-scale discriminator with padded noise fixed normal.
Otherwise route the smallest factor indicated by the exact contrast signs.

## Prohibited Actions

No model import/load/inference, checkpoint or dataset access, correction,
optimizer, training, sampler mutation, rollout, Gate C, hardware, external
compute, or Brev. This audit cannot pass Gate B or accept a policy.

## Acceptance

Tests cover exact lineage/order, metric recomputation, all contrast equations,
sign-preserving classification, non-finite values, signed identity, and every
forbidden truth flag. Writer verification must agree under Python 3.11 and 3.12.
