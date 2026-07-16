# Reviewer Decision 248 - Verify T20.36f And Route SmolVLA Design

**Decision:** `VERIFY_ACT_BOUNDARY_UNDERFIT_ROUTE_SMOLVLA_ENTRY_DESIGN`

## Reviewed Boundary

Brief 197; implementation `489be59`; pre-run `8f7cb8e`; one-use attempt
`88966621...`; result `472e5ec5...`; exact checkpoint/objective/hash replay;
per-joint and time-region summaries; verifier output; and complete scoped diff.

## Adversarial Findings

- Objective `0.0761061` and all five source hashes reproduce exactly. Direct
  and queued physical chunks are identical with maximum difference `0.0` rad.
- The miss exists before physical unnormalization. At timestep 0, normalized
  errors reach `2.64747` wrist flex and `2.44484` wrist roll, decoding to
  `0.366316` and `0.442487` rad. Shoulder lift reaches `0.125317` rad.
- Gripper reaches `0.241636` rad at timestep 49. Fourteen total exceedances
  split 9/0/0/1/4 across the five ten-step regions. The error is concentrated
  at chunk boundaries, not introduced by queued cadence or coordinate scaling.
- The shared dataset/statistics/coordinate path and ACT decode plumbing
  reproduce. The evidence localizes ACT model/optimization underfit; it does
  not prove SmolVLA will pass.
- A Gate B amendment is not justified here: shoulder-lift and gripper errors
  are task-relevant, not merely symmetric-cube wrist-roll freedom.
- No optimizer or retry ran. Result claims leave policy selection, SmolVLA
  entry execution, Gate B change, Gate C, hardware, external compute, and Brev
  false.

## Disposition

Verify T20.36f and close ACT. Open Brief 198 for design-only exact SmolVLA Gate
B entry using the local cache and a real two-camera configuration. Preserve the
unchanged gate. No model or optimizer authority is opened by this decision.

## Withheld Authority

No ACT retry, SmolVLA model/tensor access, inference, optimizer, policy
selection, Gate B amendment, Gate C, rollout, hardware, external compute, or
Brev.
