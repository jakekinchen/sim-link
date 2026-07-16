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
