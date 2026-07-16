# Reviewer Decision 280 - Verify T20.39a Receipt And Archive Hardening

**Decision:** `VERIFY_FAIL_CLOSED_RECEIPT_ARCHIVE_HARDENING_AMEND_CLOSEOUT`

## Reviewed Boundary

Brief 211; implementation `83d51c52d47b937a27df625df93f9043b69c84cd`
on origin; amended T20.38 receipt `042bf0be...`; amended T20.39 receipt
`60babc53...` and index `043d45b3...`; exact regeneration/verification CLIs;
24 strict-v2/T20.19/T20.38/T20.39 tests; 12 project-pointer tests; JSON,
compilation, whitespace, branch, ancestry, and origin-parity checks; and the
complete scoped diff.

## Findings

- Raw and normalized comparator margins remain unchanged measurements. Failed
  actor/evidence guards are now an explicit blocker list and preempt the
  effective bottleneck, so a positive numeric margin cannot hide an invalid
  proof surface.
- T20.38 now tests a truly absent bound source and a direct contradiction
  between a valid compiled conjunction and the declared evaluator result.
- Every archived receipt is schema/task/fingerprint checked; semantic-core,
  cell, predicate, and trace evidence must agree with top-level fields.
- Replay, policy-blame, replay-gate, and training flags must agree with the
  routing class, policy ownership, and remotely retained trace state. Signed
  top-level escalation fails.
- Same-fingerprint duplicate references may change only sequence/id/lifecycle/
  canonical-reference/signature fields. Any other difference is a conflicting
  duplicate and fails, including non-active references.
- Missing or drifted source bytes deterministically require lifecycle
  `invalid`, disable replay, and forbid history deletion.
- The regenerated examples preserve their proof boundaries: T20.38 is still an
  analytic-expert fixture receipt; T20.39 seed `cex-0001` is still an
  evidence-only source-controller negative with no remotely retained trace.

## Disposition

Verify Brief 211 and amend the verifier-completeness claims in Reviewer 278 and
Reviewer 279. Their operational conclusions remain unchanged: T20.38 grants no
policy/MuJoCo/physical proof, T20.39 grants no replay/training/policy blame,
T20.40 remains deferred, and T20.41 remains blocked on an owner-selected
capability route. Treat the amended receipt/index identities as current.

## Withheld Authority

No model construction/load/inference, optimizer, training, simulation or
policy replay, Gate C, replay-gate activation, training ingestion, policy
blame, source rewrite, hardware/camera/serial access, network/download,
external compute, Brev, promotion, or destructive deletion.
