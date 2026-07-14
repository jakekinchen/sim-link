# Slice Brief 125 - T20.5 PI0.5 Execution-Horizon Sweep

**Date:** 2026-07-14

## Objective

Isolate whether PI0.5 open-loop action queue duration explains the gap between
the T20.4 500-update adapter's low held-out loss and zero-contact closed-loop
behavior. Compare horizons 5, 10, and 15 with every other model, source, seed,
and semantic-proof input fixed.

## Contract

- Revalidate central simulation authority before model load. Use the exact
  T20.4 500-update adapter and training summary; no optimizer runs are allowed.
- Fix held-out episode seed 2, inference seed 1703, ten denoising steps, prompt,
  processor, postprocessor, canonical coordinates, and 244-frame phase plan.
- Parameterize only `n_action_steps` to 5, 10, or 15. Record the initial policy
  reset count, queue-refill/replan count, and maximum open-loop duration.
- Reuse the signed T20.4 horizon-5 artifact after verifying its identities and
  runtime fields. Produce fresh immutable horizon-10 and horizon-15 artifacts.
- For every horizon retain all strict-v2 measured gate margins, terminal
  outcome, assist/projection counts, policy action-sequence hash, and five
  256 px top/wrist keyframes. No result is promoted from loss or motion alone.

## Acceptance Criteria

- All three artifacts bind the same adapter, run summary, source, inference
  seed, held-out seed, and proof gates; only the action horizon may differ.
- Queue refill counts equal `ceil(244 / horizon)` and exactly one initial policy
  reset is recorded.
- The review identifies whether any horizon changes contact/lift margins or
  closes the queue-duration hypothesis as negative.

## Out Of Scope

Further training, altered inference seeds, changed denoising steps, hardware,
external compute, Brev, promotion, and physical transfer.

## Verified Outcome

Fresh horizon-5, horizon-10, and horizon-15 artifacts record one initial policy
reset and 49, 25, and 17 queue refills respectively. The fixed adapter and seed
produced three distinct action-sequence hashes. Nevertheless, all three
rollouts made zero strict-v2 contacts, used zero assist and zero projections,
and lifted exactly 0.00000030070669393422733 m against the 0.025 m gate. Each
retains five 256 px keyframes and all measured gate margins. Reviewer 154 closes
the execution-horizon hypothesis as verified negative evidence.
