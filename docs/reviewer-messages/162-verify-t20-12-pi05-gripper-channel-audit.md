# Reviewer Decision 162 - Verify T20.12 PI0.5 Gripper-Channel Audit

`CONTINUE`

Reviewed implementation boundary `b1170e14287d899d3fdb93345301eb1bba68b7cd`
and audit identity
`12aacb3c5aa7010254fc73407931adf740f2d0662764d836a166984c26319921`.

The audit binds the exact T20.1 tensor view, T20.7 PI0.5 checkpoint and
training result, T20.11 localization result, pinned pre/postprocessor files,
normalizer statistics, coordinate code, loss code, and unified LeRobot stack.
All 732 source actions round-trip through conversion and normalization within
3.606e-9 rad versus the 1e-8 rad limit. Float32 tensor quantization accounts
for the 2.384e-8 rad difference from the immutable source action and does not
explain T20.11's 0.75432 rad gripper error.

The same-agent adversarial review found no sign inversion, clipping, action
reordering, train/held-out substitution, normalized/native confusion, omitted
loss weighting, non-finite value, source alias, or authority escalation. Tests
reject each of those drift classes. The exact loss source gives all six
dimensions weight 1.0, so gripper underweighting is not observed.

The supported finding is a broader checkpoint-normalizer domain mismatch, not
a single gripper fault and not a proven causal training result. Four channels
exceed checkpoint min/max: shoulder lift, wrist flex, wrist roll, and gripper.
Continue to a train-only dataset-bound state/action normalizer preflight, with
held-out statistics used only for evaluation and no optimizer in that slice.
Do not accept a policy or grant hardware, physical transfer, promotion,
external-compute, or Brev authority.
