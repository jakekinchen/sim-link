# Reviewer Decision 238 - Verify T20.35x Gate B Pass

**Decision:** `VERIFY_GATE_B_PASS_ROUTE_T20_36`

## Reviewed Boundary

Brief 190; implementation commits `1c0fc1a` and `ff36b1b`; pre-run Decision
237; consumed attempt `48e6e24a...`; signed run `b5cc16ef...`; checkpoint
`40c94f66...`; signed result `e79dacff...`; exact verifiers; source tree;
result commit `afa421d`; and the complete scoped evidence.

## Adversarial Findings

- Exactly 500 paired updates completed with finite component objectives and
  gradients. The 50 correction examples were used ten times each and all 500
  standard replay seeds were unique.
- The exact T source checkpoint remains byte-identical. The X checkpoint is a
  distinct content-addressed tree; no source, dataset, statistics, processor,
  or sampler was mutated.
- The final standard objective is `0.002418913`, or `0.002522121` of the
  original `0.959079105` Gate B baseline, below the unchanged 0.10 threshold.
- All five decoded chunks pass 0.05 rad. Maximum errors are `0.0375184`,
  `0.0350866`, `0.0447848`, `0.0438771`, and `0.0386662`; the worst margin is
  `0.00521515` rad.
- Joint-weighted and time-and-joint-weighted correction ratios pass their 0.10
  targets at `0.0368839` and `0.0358318`.
- The raw unweighted correction ratio is `0.319203` and fails its auxiliary
  target. The signed result correctly leaves
  `all_correction_objective_ratios_within_target=false`. It does not conceal
  or relabel that limitation.
- Gate B is defined by the standard-objective ratio and all decoded-action
  errors. Both conjuncts pass, so `gate_b_passed=true` is mechanically valid.
- No closed-loop rollout occurred. Gate C, simulation policy acceptance,
  physical transfer, promotion, hardware, external compute, and Brev remain
  closed.

## Disposition

Verify T20.35x as the first Gate B pass. Open T20.36 under Brief 191 for one
separately reviewed bounded corrected-coverage campaign. Require Gate B
retention before a training-seed Gate C reproduction, and require Gate C
before held-out seeds 6 and 7. No additional model, optimizer, or rollout
authority is granted by this decision.
