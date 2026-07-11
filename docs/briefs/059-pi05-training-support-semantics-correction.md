# Slice Brief 059 - PI0.5 Training-Support Semantics Correction

**Date:** 2026-07-11

## Objective

Correct Brief 058's overly broad interpretation of PI0.5 mean/std-normalized
state outside `[-1, 1]` as automatically invalid, and replace it with a
machine-verifiable audit of the exact checkpoint's observed training support.

## Contract

- Reverify the Brief 056 source contract, Brief 057 blocked reviewed-input
  gate, Brief 058 deterministic fixture, exact checkpoint config, serialized
  preprocessor, and content-addressed normalizer state.
- Treat serialized `STATE = MEAN_STD` as the trained checkpoint semantics. The
  source default of `QUANTILES` must not override the checkpoint, and this
  slice must not silently clamp, renormalize, change bins, switch modes, or
  mutate processor/tokenizer behavior.
- Parse and bind the six-wide `mean`, `std`, `min`, `max`, `q01`, `q10`,
  `q50`, `q90`, and `q99` state statistics from the already pinned normalizer
  file. Reject missing, malformed, non-finite, nonordered, duplicate, or
  re-signed substitutions.
- Record that `[-1, 1]` is the fixed textual discretizer reference interval,
  not a hard input-validity domain for this mean/std-trained checkpoint. Preserve
  exact `np.digitize(...)-1` saturation behavior and the already observed prompt
  tokens.
- Classify each fixture joint independently against mean±std, q01-q99, and the
  observed training min-max envelope. Do not treat a value beyond one standard
  deviation as absent from training support.
- Correct the fixture conclusion: wrist-flex is below the observed training
  minimum and q01; gripper is above one standard deviation but remains within
  q01-q99 and observed min-max support.
- Emit and independently verify a versioned corrected fixture parity artifact.
  It may grant only fixture preprocessing/training-support conformance. It must
  not grant a real reviewed input, static-pose acceptance,
  `policy_shadow_input_valid`, policy shadow, replay, model/weight access,
  hardware, actuation, qualification, transfer, promotion, or training.
- Add adversarial tests for silent normalization-mode or clipping changes;
  `[-1,1]` hard-domain relabeling; statistic-file, tensor, joint-order, support-
  class, prompt-bin, and source drift; gripper false rejection; wrist-flex false
  acceptance; and every authority escalation.

## Evidence and authority

This is a correction to fixture interpretation, not a new general evidence
layer and not a policy run. Do not instantiate a model, name or read model
weights, infer, postprocess actions, access hardware, replay, train, or start
paid compute. The current parent remains live-ineligible; the live gate and
`training_lock` remain closed.
