# Reviewer Decision 246 - Verify T20.36e Negative ACT Control

**Decision:** `VERIFY_NEGATIVE_ACT_CONTROL_ROUTE_EXACT_DECODE_LOCALIZATION`

## Reviewed Boundary

Brief 196; pre-run commit `445c016`; attempt `5c971d1a...`; complete signed run
`9911e51c...`; result `2ea2c246...`; checkpoint `01b57134...`; exact runner
verification; all six scheduled evaluation rows; and current output files.

## Adversarial Findings

- The only attempt ran exactly 2,000 updates. Every objective and pre-clip
  gradient norm is finite; the declared failed-run schedule is complete.
- Objective falls from `1.385815` to `0.0761061`, so the ratio passes at
  `0.054918`. All five final repetitions hash to `ecaa2e4c...`.
- Mean physical error is `0.0145525` rad, but the all-element maximum is
  `0.442487` rad. Gate B therefore fails without changing the 0.05-rad gate.
- The negative result is bounded correctly: it does not prove the dataset is
  faulty, exonerate PI0.5, select ACT, authorize SmolVLA, or open Gate C.
- The checkpoint tree is safe and content-addressed; exact verification
  reproduces its config and 45,251,096-byte safe-tensor hashes.
- The aggregate run cannot identify which joint/timestep owns the maximum.
  Pre-clip norms reached `320.081`, so neither gate brittleness nor a shared
  normalization defect may be claimed without exact decoded localization.
- No network, retry, second attempt, rollout, policy acceptance, hardware,
  external compute, or Brev occurred.

## Disposition

Verify T20.36e negative and close its permit. Open Brief 197 for a separately
authorized, checkpoint-reload-only audit that reproduces the final hash and
objective, compares direct prediction with queued decoding, and records exact
normalized/physical error concentration by joint and timestep. Do not open
SmolVLA or amend Gate B before that result.

## Withheld Authority

No training retry, second ACT campaign, model load or inference under the
consumed permit, optimizer, policy selection, SmolVLA entry, Gate B amendment,
Gate C, rollout, hardware, external compute, or Brev.
