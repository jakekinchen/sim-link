# Slice Brief 051 - Stable Camera Identity Binding

**Date:** 2026-07-11

## Objective

Correct the T16.5c camera source binding before any live-candidate runner is
implemented. The accepted T16.5b manifest currently exposes only a digest of
the complete capture-time camera selection, including its volatile numeric
AVFoundation index. Preserve that attempt-specific digest for trace audit, add
an independently verified stable identity digest that excludes only the
numeric index, and migrate every dependent offline artifact to the stable
binding.

## Contract

- Advance the tracked redacted live-observation manifest to a new schema that
  exposes both the complete capture-selection digest and a stable digest over
  exact camera name, unique ID, model ID, and signed input mode.
- Exclude only the numeric AVFoundation index from the stable digest. Camera
  name, unique ID, model ID, pixel format, dimensions, and framerate remain
  identity-bearing and any change must reject.
- Recompute both digests from signed private evidence; reject missing,
  duplicate, substituted, malformed, or re-signed camera identities.
- Preserve verification of historical v4 manifests against their original
  private evidence without granting them the new stable-binding capability.
- Regenerate the accepted tracked manifest from the immutable private attempt-
  006 bundle and independently verify every private evidence/frame reference.
- Rebuild the signed CalibrationProfile, static-pose contract, deterministic
  fixture observation/result, and fixture-runtime source expectations so the
  production bracket contract consumes only the stable camera digest.
- Prove that numeric index churn preserves the stable digest while name,
  unique-ID, model-ID, and input-mode churn does not.

## Evidence and authority

This correction may preserve the existing T16.5b proof labels and grant only
`stable_camera_identity_binding_valid` as a local offline capability. It must
not grant a live bracket, synchronized observation, policy-input validity,
policy shadow, physical qualification/transfer, motion, promotion, or training.

This slice reads immutable ignored private evidence only. It must not enumerate
or open hardware, instantiate a serial/camera object, call Studio, reconnect,
write, change torque, command motion, preprocess or run a policy, run MuJoCo,
train, or start paid compute. The live gate and training lock remain closed.
