# Brief 211 - T20.39a Receipt And Archive Verifier Hardening

## Status

Active additive correction after the closeout review independently identified
two fail-closed verification gaps in the new T20.38/T20.39 model-free
contracts. Historical commits and signed artifacts remain preserved; any
replacement artifact is a new derived view, never a rewrite of its source.

## Objective

Harden quantitative-receipt guard/bottleneck semantics and counterexample
archive duplicate/routing/source-lifecycle verification so the exact acceptance
claims in Briefs 209 and 210 are mechanically enforced before the morning
closeout is treated as final.

## Required Corrections

1. T20.38 must test an actually missing bound source and a genuine
   evaluator-versus-compiled-conjunction contradiction, not only unsigned
   source drift.
2. T20.38 must expose actor/evidence guard blockers separately from raw numeric
   margins and define an effective bottleneck that cannot hide a failed hard
   guard behind a positive comparator margin.
3. T20.39 archive validation must cross-check all top-level replay,
   policy-blame, replay-gate, and training flags against the routing matrix,
   source retention, and policy-owned evidence.
4. T20.39 duplicate references may differ only in archive sequence, receipt
   identity, lifecycle, and canonical-reference fields. Any other difference
   under the same semantic fingerprint is a conflicting duplicate and fails.
5. T20.39 must emit deterministic missing/stale-source lifecycle evidence that
   requires `invalid`, disables replay, and forbids history deletion.

## Acceptance

- Tests cover missing source, genuine contradiction, hard-guard bottleneck
  precedence, top-level routing escalation, conflicting inactive duplicates,
  deterministic ordering, and missing/stale lifecycle disposition.
- Regenerated example artifacts reconstruct exactly and retain their truthful
  analytic-fixture/evidence-only proof boundaries.
- Existing T20.36o result identities and all source artifacts are unchanged.
- Focused plus relevant broad tests, exact CLI verification, same-agent
  adversarial review, canonical pointers, explicit-path commits, push, and
  origin confirmation all agree.

## Prohibited Actions

No model construction/load/inference, optimizer, training, simulation or policy
replay, Gate C, replay-gate activation, training ingestion, policy blame,
source rewrite, hardware/camera/serial access, network/download, external
compute, Brev, promotion, or destructive deletion.
