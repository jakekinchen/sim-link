# Slice Brief 058 - PI0.5 Fixture Model-Ready Tensor Parity

**Date:** 2026-07-11

## Objective

Prove, entirely offline and without constructing a policy or reading model
weights, that one accepted-review-shaped deterministic static-pose fixture is
transformed through the pinned physical-observation preprocessing path into
the exact bytes and tensors that the PI0.5 model-input boundary would receive.

## Contract

- Reverify the exact Brief 056 preprocessing source contract and Brief 057
  reviewed-input issuance gate. The real gate remains blocked; this slice may
  use only a separately classified `deterministic_fixture` review shape.
- Rebuild and re-evaluate the checked static-pose fixture through the signed
  calibration and static-bracket contracts. Select `q_after` in the declared
  six-joint order and preserve degrees for the five body joints and percent for
  the gripper.
- Create four deterministic complete RGB PNG byte streams representing two
  frames for each signed camera identity. Bind the fixture camera identities
  bijectively to `observation.images.top` and
  `observation.images.wrist`, select the highest complete frame index for each
  role, and record both encoded-byte and decoded-RGB hashes.
- Load only the exact cached checkpoint preprocessor and exact cached tokenizer
  pinned by Brief 056, in strict offline mode, with the signed CUDA-to-CPU
  device override as the sole semantic configuration mutation. Do not name,
  stat, open, or read any model-weight file.
- Run the actual pinned rename, batching, normalizer, PI0.5 state-prompt,
  tokenizer, and device steps. Record canonical hashes, shapes, dtypes,
  devices, and bounded summaries for every model-facing output.
- Exercise the exact pinned model image-preprocessing method without
  constructing a policy: resize each selected 640x480 RGB input with padding
  to 224x224, convert `[0,1]` to `[-1,1]`, preserve checkpoint camera order,
  and materialize the absent right-wrist input as a `-1` tensor with a false
  mask. Record all image tensor and mask hashes.
- Pin the checkpoint action representation, joint order, chunk size, action
  horizon, and reset-before-sample queue requirement without creating a model,
  action queue, action proposal, or postprocessed action.
- Emit and independently verify one deterministic checked-in fixture artifact.
  It may grant only `fixture_pi05_model_ready_tensor_parity_conformant`; it must
  grant no live acceptance, policy-input-valid, policy-shadow, replay,
  actuation, qualification, transfer, promotion, or training authority.
- Add adversarial tests for source/gate/static-result drift; fixture-to-live
  relabeling; camera role/order/frame-selection ambiguity; PNG corruption;
  state order/unit/selection drift; prompt/token/tensor metadata or digest
  drift; missing-camera mask escalation; action/horizon/reset drift; false
  model, weight, network, hardware, inference, replay, or authority claims.

## Evidence and authority

The current parent remains mechanically live-ineligible. Do not access serial,
camera, Studio, or robot hardware; do not instantiate PI0.5, inspect weight
files, infer, postprocess actions, replay in MuJoCo, train, or start paid
compute. The live gate and `training_lock` remain closed. Completion answers
only: "Do we know exactly what fixture bytes and tensors PI0.5 would receive?"
