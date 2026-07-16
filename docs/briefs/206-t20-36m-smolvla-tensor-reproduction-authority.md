# Brief 206 - T20.36m SmolVLA Tensor Reproduction Authority

## Status

Active under the owner's 2026-07-16 eight-hour continuation authorization.
The execution window is 01:44:12-09:44:12 CDT with no new major slice after
08:59:12. This activates only the requested local simulation/model authority
below; it does not grant optimizer, Gate C, hardware, network, external-compute,
or Brev authority.

## Objective

Reproduce and persist only the already-evaluated final SmolVLA 50x6 physical
action tensors from the immutable T20.36j checkpoint, prove all five fixed-seed
hashes match the signed T20.36j run, and score those tensors under frozen
T20.36l Gate B. This is inference-only evidence recovery, not a retry, new
candidate, optimizer run, or Gate C attempt.

## Requested Owner Authority

- Construct and load the exact retained T20.36j SmolVLA checkpoint locally.
- Run exactly the five registered inference seeds with two repeats each on the
  canonical one-batch observation, under the existing offline/MPS/no-fallback
  guards.
- Persist the ten 50x6 physical action tensors and require their hashes to equal
  the five already-signed T20.36j pairs before scoring frozen Gate B.
- Stop after a hash mismatch, runtime failure, or the frozen Gate B decision.

## Required Work After Authority

1. Compose a fresh central inference authority decision and one-use permit
   bound to T20.36j checkpoint `32f0bd30...`, run `7e7304c5...`, frozen gate
   `463477dc...`, and result `0f8ae393...`.
2. Construct the exact cached model once with network and fallback prohibited.
3. Reproduce ten tensors and prove hashes, repeat equality, shape, coordinate
   conversion, and finite values before retaining them.
4. Score every joint/timestep under frozen reach/grasp thresholds. Candidate
   errors cannot change the thresholds.
5. If SmolVLA passes, route only to a separate one-training-episode Gate C
   authority request. If it fails, close the learned-policy Gate B branch.

## Prohibited Actions

No optimizer, training update, checkpoint mutation, new seed, third repeat,
threshold change, ACT work, Gate C execution, policy acceptance/promotion,
hardware, network/download, external compute, or Brev.
