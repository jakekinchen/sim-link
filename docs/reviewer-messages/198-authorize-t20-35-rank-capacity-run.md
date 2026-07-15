# Reviewer Decision 198 - Authorize One T20.35 Rank-Capacity Run

**Decision:** `CONTINUE_ONE_T20_35_RANK_16_RUN`

## Reviewed Boundary

Brief 166, implementation `579855f`, the signed specification, owner-scope
grant, central composition, runner, tests, canonical state, and complete scoped
diff were reviewed together after remote preservation.

## Adversarial Findings

- The T20.35 specification is mechanically derived from the frozen T20.33
  artifact and fails closed on every material change except rank/alpha 4 to 16.
- Learning rate, update count, batch, source seed, inference seeds, action
  horizon, processors, base revision, task, and gates are unchanged.
- The decision grants only `simulation_training_ready` and expires at the
  current hard closeout. It grants no retry, continuation, second rank, second
  batch, closed-loop rollout, hardware, external compute, Brev, transfer, or
  promotion.
- Non-finite objectives and gradients, checkpoint drift, target-module drift,
  seed drift, authority drift, and forbidden result fields fail closed.
- The initial runner inherited T20.33's late run-directory creation, which
  could have allowed a retry after a mid-run failure. The reviewed version now
  writes a signed immutable attempt marker before model construction; any
  failed attempt consumes the one-run permit.
- Existing user-owned config changes and external checkouts are excluded.

## Disposition

After this decision is committed, pushed, and confirmed on
`origin/codex/pi05-autolearn-loop`, execute exactly one local-MPS rank-16 run.
Then compose and verify one signed result. Do not retry or continue regardless
of outcome. Route a pass to the separately reviewed bounded campaign and a
failure to the conditional T20.35.x evidence ladder.
