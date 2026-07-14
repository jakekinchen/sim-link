# Slice Brief 139 - T20.17 Actual LeRobot Processor Observation

**Date:** 2026-07-14

## Objective

Replace the shadow-preprocessing contract's core responsibility with a small
observation of the pinned package pipeline itself. A source-bound actual
`LeRobotDataset` sample enters the pinned PI0.5 preprocessor, and the signed
result records only the actual finite outputs and serialized pipeline files.

## Contract

- Re-verify the signed native episode manifest before selecting the requested
  source frame; bind its full episode content hash, package metadata identity,
  and raw-rollout/eligibility annotation to the observation.
- Load `DataProcessorPipeline` only from explicitly supplied local pinned
  checkpoint and tokenizer directories with network disabled, and record its
  actual step class order plus hashes of its serialized config/step/tokenizer
  files. The tokenizer path override changes only the offline source location,
  not processor behavior.
- Run the processor once on the package-returned sample. Hash output values
  exactly as returned; do not implement normalization, renaming, tokenization,
  image handling, or state padding in SceneSmith.
- The slice may not instantiate a policy/model, create actions, mutate dataset
  files, run an optimizer or simulator, or touch hardware, external compute,
  or Brev.

## Acceptance Criteria

- A real temporary `LeRobotDataset` and the cached pinned PI0.5 processor
  produce deterministic repeated signed observations with the actual six-step
  pipeline order and finite output descriptors.
- Tampering with a signed observation, source annotation, dataset metadata,
  pipeline file, or output causes verification failure.
- Output reports that the processor ran but model, inference, optimizer,
  simulator, hardware, external compute, and Brev did not.

## Out Of Scope

Replacing historical fixture artifacts in place, training, checkpoint/model
loading, postprocessor/action execution, policy rollout, hardware, external
compute, and Brev.
