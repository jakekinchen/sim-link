# Slice Brief 056 - PI0.5 Preprocessing Source Contract

**Date:** 2026-07-11

## Objective

Implement and verify, entirely offline, a fixture-only signed contract that pins
the exact executable PI0.5 preprocessing sources and checkpoint processor
artifacts while mechanically recording every missing real-observation input.
The slice must make later preprocessing reproducible without preprocessing any
live observation, loading model weights, or running inference now.

## Contract

- Reverify the signed robotics dependency lock, unified executable stack,
  calibration/static-pose sources, and the exact LeRobot PI0.5 configuration,
  model-input, processor, and relative-action source files by path, size, and
  SHA-256.
- Pin the cached `Cache-SCA/pi05_teleop_sort_block` processor snapshot by exact
  Hugging Face revision. Rehash its config, pre/postprocessor JSON, and normalizer
  state files through cache-contained symlink targets; exclude and do not open
  model weights.
- Parse the safetensors header and only the bounded float32 state/action count,
  mean, and standard-deviation vectors with the standard library. Require six
  finite joint statistics, positive counts/stddevs, exact feature identities,
  valid offsets, and complete file coverage.
- Pin the cached `google/paligemma-3b-pt-224` tokenizer snapshot, files, and
  tokenizer step semantics. Do not instantiate the tokenizer or access the
  network.
- Validate exact processor order, feature shapes, six-joint order, degrees for
  five body joints, normalized percent for the gripper, MEAN_STD state/action
  normalization, 224x224 image inputs, 50-action chunk, and source CUDA device.
  Derive an effective preprocessing-only config whose sole checkpoint mutation
  is the reviewed final device step from CUDA to CPU.
- Record unresolved production inputs mechanically: no accepted Brief 055 live
  review manifest/decision, no reviewed stable-camera-to-top/wrist role binding,
  and no reviewed task prompt. Keep production issuance and preprocessing
  blocked until all are supplied and verified.
- Emit and independently verify one deterministic checked-in
  `blocked_missing_inputs` artifact. Re-signing source, coordinate, processor,
  device-override, blocker, or authority drift must fail.
- Add adversarial tests for cache escape/symlink substitution, revision drift,
  file/hash/config/step/order/device drift, malformed safetensors headers and
  offsets, boolean/non-finite/wrong-width stats, tokenizer drift, camera-role or
  task fabrication, fixture/live relabeling, and authority escalation.

## Evidence and authority

The checked-in artifact may grant only
`pi05_policy_input_preprocessing_source_contract_conformant`. It must state that
no accepted live review artifact exists, no policy input was built, no tokenizer
or model was instantiated, no weights were loaded, and no preprocessing,
inference, shadow action, replay, or actuation occurred.

Do not read `model.safetensors`, construct a policy/tokenizer/processor, decode
private frame bytes, access hardware, call Studio, reconnect, write, change
torque, command motion, run MuJoCo, train, or start paid compute. The live gate
and training lock remain closed.
