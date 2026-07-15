# Reviewer Decision 244 - Verify T20.36d Exact ACT Control Design

**Decision:** `VERIFY_EXACT_ACT_CONTROL_DESIGN_ROUTE_PRE_RUN_IMPLEMENTATION`

## Reviewed Boundary

Brief 195; T20.36c, T20.33, and T20.23 signed sources; source-bound ACT
configuration/model/processor code; spec `45c90dc0...`; implementation commit
`b8b19cd`; deterministic tests; and the complete scoped diff.

## Adversarial Findings

- Episode 0's raw identity matches the T20.33 source exactly. State/action
  order, two camera features, horizon 50, and T20.23 statistics are pinned.
- The ACT is fresh and compact. Cached ACT weights, pretrained backbone,
  network fallback, VAE stochasticity, dropout, and a scheduler are disabled.
- The 0/100/250/500/1,000/2,000 schedule is fixed before the result. The sole
  future run stops at the first post-baseline pass or the 2,000-update ceiling.
- Five action repetitions must hash identically. The unchanged 0.05-rad
  physical maximum and 0.10 supervised-objective ratio both gate every
  candidate; proxy substitution and gate amendment are forbidden.
- Pass/fail claims are bounded. A pass exonerates only this shared one-batch
  statistics/round-trip path; a fail does not by itself prove a dataset fault.
  ACT is not selected as a product policy and cannot unlock Gate C.
- Twenty-eight relevant tests pass; exact verification, lint, compilation, and
  diff checks pass. All execution and authority fields remain false.

## Disposition

Verify T20.36d. Open Brief 196 to implement and remotely preserve the exact
runner, attempt/result contracts, dependency preflight, and task-specific
central authority. No attempt marker or model construction may occur before a
fresh review confirms that boundary on origin.

## Withheld Authority

No attempt, model, inference, optimizer, ACT run, policy selection, SmolVLA
entry, Gate B change, Gate C, rollout, policy acceptance, hardware, external
compute, or Brev.
