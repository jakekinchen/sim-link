# Reviewer Decision 266 - Verify T20.36n X Mixed Negative and Route Bridge

**Decision:** `VERIFY_X_MIXED_NEGATIVE_ROUTE_BOUNDED_EPISODE_BRIDGE`

## Reviewed Boundary

Brief 207; owner priority directive; frozen amendment `463477dc...`; source X
spec `96efc6d3...`, checkpoint `40c94f66...`, and five action hashes; central
decision `5b40131b...`; one-use permit `2c6a1e78...`; attempt `141fc0ba...`;
tracked tensor artifact `9d7a517a...`; run `95e2279a...`; final result
`f8d7866e...`; result boundary
`a20f2a4de1b4d8ec7f12142015d44bdecff6a345`; exact fresh-checkout tensor
rescore; 31 focused/current/pointer tests; branch/remote parity; and the
complete scoped evidence boundary.

## Findings

- All five signed T20.35x decoded-action hashes reproduce exactly and the two
  repeats for every seed are bit-identical.
- The full five-by-50-by-6 tensor payload is tracked and independently
  rescored. Its identity is `9d7a517a...`; no ignored-only evidence is needed.
- The retained verifier preserves the archived signed spec and its internal
  correction-example hash while tolerating only `5e-14` absolute rebuild drift
  in derived float leaves. This fixes dependency-reduction-order brittleness;
  structural, identity, hash, and gate mutations still fail closed.
- The retained objective ratio is `0.0025221206`, and every seed passes the
  original uniform 0.05-rad Gate B.
- Frozen amendment `463477dc...` passes seeds 0, 3, and 4 and fails seeds 1 and
  2. All five violations are grasp-phase gripper cells at timesteps 33-36.
  Their threshold excesses are `0.00034185`, `0.00041026`, `0.00062616`,
  `0.00315781`, and `0.00441953` rad. There are no arm or reach violations.
- This is the owner-authorized localization audit. It is a valid exact
  amended-gate negative and does not justify a T20.36n retry, threshold fit, or
  immediate Gate C rollout.
- Owner priority 3 explicitly re-designates X as eligible for a bounded
  episode-0 bridge after SmolVLA failure. Therefore the Gate C route remains
  open while Gate C execution remains closed until bridge acceptance.
- The bridge must use actual PI0.5 queue semantics at `n_action_steps=50`, one
  queue reset, starts 0/50/100/150/200, executed lengths 50/50/50/50/44, and
  exclusion of the last chunk's six unexecuted tail actions from acceptance
  and actor-valid evidence.
- No optimizer, training, new inference, threshold change, Gate C execution,
  hardware, network, external compute, or Brev action occurred in review.

## Disposition

Verify T20.36n as an exact mixed-negative. Close its one-use permit and do not
retry it. Activate Brief 208/T20.36o for a model-free execution-contract,
episode-window, correction-schedule, and authority design. Gate C execution may
be requested only after every executed action at all five registered
chunk-start states passes frozen amendment `463477dc...`.

## Withheld Authority

No model construction/load/inference, optimizer/training, threshold change,
Gate C rollout, policy selection/promotion, physical hardware, network,
external compute, or Brev until a separate central authority and reviewed
permit grant the exact next action.
