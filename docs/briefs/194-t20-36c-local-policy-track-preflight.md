# Brief 194 - T20.36c Local Policy-Track Preflight

## Objective

Determine whether the pinned local LeRobot source, local model cache, and
canonical T20.23 dataset already support an ACT diagnostic control and a
SmolVLA Mac-first Gate B entry without downloading, loading, or training a
model.

## Inputs

- Pinned `external/lerobot` source and its existing local environment metadata.
- Existing local Hugging Face cache metadata only; no network or tensor read.
- T20.23 recovery-dataset manifest, metadata, statistics, feature schema,
  camera keys, six action/state dimensions, and 50-step action horizon.
- Existing T20.2 ACT artifacts and the T20.35x/T20.36 Gate B contract chain.

## Required Audit

Emit one deterministic signed report that records:

1. exact LeRobot source identity and whether ACT and SmolVLA policy/config/
   processor/training entrypoints exist;
2. whether complete local model/config/tokenizer cache metadata exists for any
   candidate, without opening weight tensors;
3. exact dataset feature compatibility and any required adapter or statistics
   boundary for ACT and SmolVLA;
4. MPS-relevant source declarations and unsupported CUDA-only assumptions;
5. the smallest separately reviewed next step, with ACT ordered before
   SmolVLA when a shared-pipeline diagnostic remains useful.

## Acceptance

- No network, checkpoint tensor, model construction, inference, optimizer,
  dataset mutation, or rollout occurs.
- Missing cache or source support fails closed and cannot be relabelled as
  policy viability.
- The report may route a design brief only. It cannot select a primary policy,
  authorize training, or change Gate B.
- Deterministic tests, lint, workflow audit, same-agent review, scoped commit,
  push, and remote confirmation agree.

## Prohibited Actions

No downloads, model/checkpoint load, inference, optimizer, training, policy
selection, Gate B amendment, Gate C, hardware, camera, serial, external
compute, A100, or Brev.

## Result Boundary

Signed report `61fcf124...`, preserved at implementation commit `139fe32`,
verifies local metadata readiness only. ACT has prior MPS execution evidence
and exact-control design prerequisites, but its cached candidate is not
drop-in compatible. SmolVLA's base/VLM cache metadata is complete, but the
cached processor expects three cameras and SmolVLA MPS runtime remains
unverified. No checkpoint tensor was opened. Reviewer 243 verifies Brief 194
and routes only the exact ACT Gate B control design in Brief 195.
