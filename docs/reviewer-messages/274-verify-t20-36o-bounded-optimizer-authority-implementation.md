# Reviewer Decision 274 - Verify T20.36o Optimizer Authority Implementation

**Decision:** `VERIFY_BOUNDED_OPTIMIZER_AUTHORITY_IMPLEMENTATION`

## Reviewed Boundary

Brief 208; optimizer spec `50e0569d...`; the separate owner grant, central
composer, runtime preflight, one-use permit, attempt-marker, and materializer
implementation; four focused optimizer spec/authority tests; 31 combined
authority/contract/design/pointer tests; prospective composition; Python
compilation; and the complete scoped diff.

## Findings

- Prospective owner grant `dee9ae59...` authorizes one local simulation-only
  attempt with 250 examples, ten uses each, and 2,500 updates maximum.
- Prospective request `c325cb12...` composes to decision `8834322d...`; the
  central composer grants only `simulation_training_ready`.
- The preflight requires exact X checkpoint bytes/tree, frozen-base snapshot,
  Python 3.12/MPS stack and dependency versions, at least 8 GiB free, HEAD/origin
  parity, and absence of attempt/result/output-checkpoint paths.
- The permit copies all 2,500 correction indices and unique replay seeds from
  spec `50e0569d...`, binds probes 500/1000/1500/2000/2500, and requires first
  confirmed complete pass to stop.
- The update-0 baseline is reused from `e6537428...`; it is not decoded again.
  Each later probe is fixed to five starts, five seeds, and two repeats.
- The attempt marker must precede source-checkpoint tensor read, model
  construction, and optimizer creation. Retry and Gate C stay false.
- Any schedule mutation, repeated replay seed, stale output, insufficient disk,
  wrong runtime, remote drift, or expanded composer grant fails closed.
- No owner/request/decision/preflight/permit artifact, model, optimizer,
  checkpoint, or training action exists at review time.

## Disposition

Verify implementation only. Commit, push, and origin-confirm this boundary;
then materialize and separately review the exact authority/preflight/permit
artifacts before implementing or running the optimizer.

## Withheld Authority

No authority artifact before remote preservation, no model construction/load,
no optimizer creation/training, no checkpoint mutation, no Gate C, no retry,
no hardware, no network, no external compute, and no Brev.
