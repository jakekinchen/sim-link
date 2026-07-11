# Session 086 - Brief 056 PI0.5 Preprocessing Source Contract

**Date:** 2026-07-11

Brief 056 began offline at `2026-07-11T15:54:21-05:00`; start boundary
`011b22d6aebe9d886d7713db05491ad657086923` recorded the exact fixture-only
scope. A concurrent owner documentation commit advanced the shared branch to
`1948f5581a957c526cf4cf33802b6084778d7a12` before implementation. That work
was preserved untouched and became the implementation parent. Implementation
`fd4982097961d8df34435e2db5fd7c4397f050d4` is present on
`origin/codex/pi05-autolearn-loop`.

The new contract reverifies the dependency lock, unified executable stack,
runtime processor contract, parsed calibration profile, and static-pose
contract. It binds four exact PI0.5 source files, the checkpoint processor
snapshot and five required processor/config/statistics files, and the PaliGemma
tokenizer snapshot and five required tokenizer files. Cache evidence accepts
only the exact revisions and regular snapshot directories with files contained
as regular files or symlinks into each model cache's real blobs directory.

The safetensors path is limited to one megabyte, checks stable file identity
while reading, rejects duplicate header keys and invalid tensor layouts, and
requires complete, gap-free byte coverage. It decodes only the six required
F32 state/action count, mean, and standard-deviation vectors. The preprocessor
and postprocessor state files are byte-identical, contain 94,568 samples, and
have finite positive six-wide statistics. Values remain absent from the tracked
artifact.

The checkpoint contract fixes the three image features, six-output action
shape, 32-wide declared state/action bounds, 50-action chunk, absolute actions,
MEAN_STD normalization, tokenizer semantics, prompt template, and exact
pre/postprocessor step order. The only derived change is the final
preprocessing device from source CUDA to CPU; source and effective identities
are both recorded. Physical coordinates remain five degree-valued body joints
plus a normalized-percent gripper in the exact six-joint order.

The generated artifact is deliberately `blocked_missing_inputs`. It contains
no accepted Brief 055 live-session decision, no stable-camera-to-top/wrist role
mapping, and no reviewed task prompt. It contains no absolute cache path or
model-weight filename, and explicitly records no model/tokenizer/processor
construction, policy input, preprocessing, shadow, inference, replay, hardware,
or follower command.

Same-agent adversarial review added all-ancestor alias rejection, stable hashing
around parsed sources, complete safetensors coverage, integer count semantics,
an actual-newline prompt binding, and explicit no-model/no-shadow/no-network
facts. Tests cover source/revision/config/order/device drift, cache and tracked
source aliases, malformed/gapped/overlapping/boolean/non-finite/wrong-width
statistics, tokenizer and coordinate drift, fixture/live relabeling, and
re-signed blocker, role, task, acceptance, and authority escalation.

One hundred fourteen focused tests pass in both `.mujoco_venv` and the pinned
LeLab runtime. All existing execution, candidate, camera-identity, calibration,
static-fixture, dependency-lock, and new source-contract verifiers pass in both
runtimes. Compilation, whitespace, privacy, source-safety, and diff checks pass.
The 313-test offline authority/twin gate passes in 70.328 seconds.

No hardware was enumerated, instantiated, or opened. No serial, camera, Studio,
reconnect, register write, torque change, motion, model weight, tokenizer,
processor, policy, MuJoCo, optimizer, training, paid compute, destructive
action, or unrelated dirty path was touched. Grant only
`pi05_policy_input_preprocessing_source_contract_conformant`; the live gate and
training lock remain closed.
