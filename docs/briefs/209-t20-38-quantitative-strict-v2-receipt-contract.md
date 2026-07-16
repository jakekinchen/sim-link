# Brief 209 - T20.38 Quantitative Strict-v2 Receipt Contract

## Status

Verified model-free filler, amended by Brief 211 / Reviewer 280.
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

## Verified Result

Implementation `f9c3682` and receipt `02268a1a...` are exact on origin. The
receipt binds strict-v2 fixture `950e7568...`, evaluator source `8dd97c79...`,
33 predicate margins, hard conjunction, and deterministic bottleneck
selection. It agrees with analytic source success while explicitly withholding
pure-policy, actual-MuJoCo, physical, training, and promotion claims. Twenty-
four tests and exact write/verify pass. Reviewer 278 verifies T20.38 and
activates Brief 210 / T20.39.

## Additive Verification Amendment

Brief 211 preserves the original receipt in history and replaces the active
derived view with `042bf0be...`. Hard actor/evidence blockers now preempt the
effective bottleneck without changing raw margins; missing-source and genuine
evaluator-contradiction cases fail closed. Implementation `83d51c5` and
Reviewer 280 amends the completeness claim while preserving the analytic-only
proof boundary.
