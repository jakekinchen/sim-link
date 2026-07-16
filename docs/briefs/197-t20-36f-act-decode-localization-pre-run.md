# Brief 197 - T20.36f ACT Decode Localization Pre-Run

## Objective

Build and remotely preserve a single inference-only audit that reloads the
exact T20.36e checkpoint, reproduces its final objective/action evidence, and
localizes the isolated physical maximum by joint, timestep, and decode path
before SmolVLA entry or any Gate B amendment.

## Frozen Inputs

- T20.36d spec `45c90dc0...`.
- T20.36e result `2ea2c246...`, run `9911e51c...`, checkpoint
  `01b57134...`, final evaluation `16d868b0...`, and decoded action hash
  `ecaa2e4c...`.
- The exact canonical episode-0 batch, T20.23 MEAN_STD statistics, coordinate
  conversion, ACT configuration, pre/postprocessors, and local LeRobot stack.

## Required Audit

1. Verify every frozen artifact and checkpoint file before model load.
2. Obtain a fresh task-specific, inference-only central boundary; commit and
   confirm it on origin before loading ACT or reading checkpoint tensors.
3. Reload the safe checkpoint once, reproduce the final supervised objective
   and five deterministic decoded action hashes, and reject any mismatch.
4. Record the normalized predicted/target chunk and decoded physical chunk only
   through bounded signed summaries: per-joint mean/maximum error, maximum-error
   joint/timestep/value, threshold exceedance counts, time-region counts, and
   finite/direct-versus-queued equality evidence.
5. Compare one direct predicted action chunk with the 50-action queue path.
   Distinguish processor/queue mismatch, normalization-to-physical scaling,
   localized endpoint/outlier error, and distributed model error without
   changing a threshold.

## Acceptance And Routing

- If checkpoint/objective/hash reproduction fails, stop on reload or runtime
  drift; do not interpret per-joint evidence.
- If direct and queue paths differ, route ACT decode/queue implementation.
- If they agree, route from the signed normalized-versus-physical per-joint and
  time distribution. SmolVLA entry requires a separate reviewer decision after
  this audit; a gate amendment requires a separately owner-signed decision.
- Preserve the negative or positive localization result on origin.

## Prohibited Actions

Before the reviewed boundary: model load, checkpoint tensor read, or inference.
Throughout: optimizer creation/training, training retry, second ACT campaign,
dataset/statistics mutation, policy selection, SmolVLA entry, Gate B change,
Gate C, rollout, hardware, camera, serial, external compute, or Brev.

## Pre-Run Evidence

- Implementation `489be59` is remotely preserved; 41 T20.36 regressions pass.
- Central decision `de30947f...` grants only the repository's central ready
  state. Owner grant `9a96cc16...` and one-use permit `d9daae7b...` restrict the
  task to one checkpoint load plus simulation inference, with optimizer and
  training retry false.
- Model-free preflight `40e24b5e...` rehashes checkpoint `01b57134...` as the
  exact 1,684-byte config plus 45,251,096-byte safe tensor, binds MPS and the
  pinned dependency/runtime identities, and confirms remote source `489be59`.
  Checkpoint tensors were not parsed and no attempt marker exists.

Reviewer Decision 247 verifies this boundary and opens its sole inference audit
only after the signed evidence and review are confirmed on origin.

## Audit Result

Signed result `472e5ec5...` reproduces the final objective and all direct/queued
action hashes exactly; direct-versus-queue physical error is zero. The largest
normalized errors already occur at timestep 0 on wrist flex (`2.64747`) and
wrist roll (`2.44484`), decoding to `0.366316` and `0.442487` rad. Shoulder
lift also reaches `0.125317` rad at timestep 0; gripper reaches `0.241636` rad
at timestep 49. Fourteen elements exceed 0.05 rad: 9 in steps 0-9, 1 in steps
30-39, and 4 in steps 40-49. This localizes sparse boundary/endpoint model
underfit before physical unnormalization, not queue/decode inconsistency.

Reviewer Decision 248 verifies T20.36f and routes Brief 198 to a design-only
SmolVLA Gate B entry boundary. ACT training is not retried and Gate B is not
amended; shoulder-lift and gripper misses make a consequence waiver premature.
