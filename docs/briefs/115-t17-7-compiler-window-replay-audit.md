# Slice Brief 115 - T17.7 Compiler Window Replay Audit

**Date:** 2026-07-13

## Objective

Audit the verified non-empty T17.5b grasp source with exactly 100 deterministic
windows. Bind each selected window to its append-only raw frames, source-bound
compiler rows, and T17.5b window-index row; then record canonical actor-input
and action descriptors for collection/training/inference-input parity without
training or model execution.

## Contract

- Inspect only the fixed T17.5b episode-store manifest and ignored append-only
  store, compiler view, and unpadded window index. Verify each existing source
  before reading it; never scan alternate stores or other ignored output roots.
- Select exactly 25 windows at each of horizons 5, 10, 15, and 50. Sampling
  must be deterministic, horizon-stratified, and cover every realized rollout
  before using additional windows. Record every selected `window_id` and its
  deterministic selection rank.
- Each selected frame must prove raw-frame record identity equals the compiler
  row identity; compiler/index frame sequence, timestamps, action-frame IDs,
  source identities, segment boundaries, and full action variants must agree.
- Materialize canonical serialized actor-input and requested-action tensor
  descriptors from the immutable raw frames. Training and inference descriptors
  must be identical for the shared actor inputs and distinct from the requested
  action target descriptor. This is input-contract parity only: it does not
  instantiate a model, execute inference, or establish trained-policy behavior.
- Write a signed tracked audit manifest containing only identifiers, shapes,
  dtypes, and hashes—never image payloads, raw action arrays, or other copied
  raw evidence. The audit and all authority flags fail closed.

## Acceptance Criteria

- A byte-identical rerun produces the same manifest and validates all 100
  selected windows, with 25 selections at every horizon and no invalid selected
  frame/window.
- Tests reject source-manifest/store/hash drift, missing or duplicate window
  selection, horizon skew, non-contiguous/timestamp-drifting frame sequences,
  raw/compiler identity mismatch, boundary crossing, incomplete action
  variants, actor-input leakage, tensor-descriptor mismatch, authority
  escalation, and any raw rewrite attempt.
- The manifest names its source hashes, selection algorithm, selected counts,
  and exact scope limitations. It remains training-, optimizer-, hardware-,
  physical-, and external-compute-ineligible.

## Out Of Scope

No model loading or inference, optimizer/training, dataset-mixture selection,
normalization change, raw-store rewrite, hardware, physical motion, Brev,
external compute, or deletion.

## Stop Conditions

Stop if the fixed T17.5b sources fail their own verification, a selected window
cannot be traced exactly to raw frames, an actor input needs conversion or
inference, or selection cannot meet all four 25-window strata without relaxing
the contract.
