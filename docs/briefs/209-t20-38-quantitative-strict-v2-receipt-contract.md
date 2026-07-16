# Brief 209 - T20.38 Quantitative Strict-v2 Receipt Contract

## Status

Active model-free filler after Reviewer 277 closes the current Gate C route.
The owner overnight direction explicitly routes T20.38 before T20.39 when no
candidate Gate C route remains.

## Objective

Define one policy-independent, deterministic, content-addressed strict-v2
receipt that reports raw signed margins and normalized margins for every
strict grasp predicate while preserving hard evidence/actor guards, bottleneck
semantics, and exact source identities. Historical artifacts remain immutable.

## Required Contract

1. Bind the exact existing strict-v2 evaluator implementation, schema, joint
   and object semantics, source trace identity, evaluator configuration, and
   evidence provenance.
2. Report each predicate's observed value, comparison direction, threshold,
   signed raw margin, normalization scale, normalized signed margin, pass
   state, and whether it is actor-valid and evidence-valid.
3. Define positive margin as pass-side distance for every direction; reject
   zero/non-finite normalization scales and ambiguous or missing comparison
   semantics.
4. Preserve hard conjunction semantics. The receipt may identify the minimum
   normalized-margin bottleneck but may not average, compensate, or promote
   across failed predicates.
5. Keep fixture, synthetic, replay, simulation, and physical provenance
   distinct. Invalid actor/evidence guards fail closed and cannot be relabelled
   as strict success.
6. Provide deterministic build/verify APIs, adversarial tests, and one
   checked-in simulation-only example derived from an existing immutable
   strict-v2 artifact without modifying that source.

## Acceptance

- Exact reconstruction produces one stable signed identity.
- Comparator direction and normalized-margin tests cover upper, lower, range,
  boolean/hard-guard, equality, non-finite, zero-scale, missing-source, and
  contradictory evidence cases.
- The example receipt identifies its bottleneck mechanically and agrees with
  the source strict-v2 conjunction.
- Focused and relevant broad tests, same-agent adversarial review, canonical
  state, scoped commit, push, and origin confirmation all agree.

## Prohibited Actions

No model construction/load/inference, optimizer, rollout, gate or threshold
change, history rewrite, policy selection, physical hardware, camera/serial
access, network/download, external compute, Brev, promotion, or destructive
operation.
