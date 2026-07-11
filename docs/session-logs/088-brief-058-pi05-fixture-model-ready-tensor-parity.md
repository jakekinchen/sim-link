# Session 088 - Brief 058 PI0.5 Fixture Model-Ready Tensor Parity

**Date:** 2026-07-11

This offline continuation began at `2026-07-11T16:47:11-05:00` from remotely
matched HEAD `3ae7c4bae798b59abc11159c2ec5ba495467d06d`. The persisted Codex Goal was
found absent and was restored at `2026-07-11T16:46:11-05:00`; a follow-up
Goal read confirmed it active in this top-level thread.

The original owner-extended hard closeout was
`2026-07-11T12:14:07-05:00` and has elapsed. The current owner-triggered
continuation has no new live run window or hardware eligibility. Brief 058 is
therefore fixture-only and offline: the live gate and `training_lock` are
closed, the active runtime parent remains approval-policy `never`, and no
hardware, model weight, policy inference, MuJoCo replay, optimizer, or paid
compute is authorized.

Starting branch, upstream, and remote were all
`codex/pi05-autolearn-loop` / `3ae7c4bae798b59abc11159c2ec5ba495467d06d`.
All unrelated modified and untracked paths were recorded and remain outside
this slice. Brief 058 will stop at deterministic fixture model-input parity;
any live static bracket still requires a fresh hardware-supervised on-request
parent, finite window, reviewed gate transition, presence lease, discovery,
and all-alias zero-holder proof.

Implementation `77724e14ba499fadb981c4099b334a19a235c51d` is present on
`origin/codex/pi05-autolearn-loop`. The checked artifact is
`configurations/robot_lab/pi05_fixture_model_ready_tensor_parity.json`, schema
`scenesmith.pi05_fixture_model_ready_tensor_parity.v1`, identity
`559b9dbd112d9df460b000e6c127d6f16200d9e89a2d418b3e8a8179e1af8732`.
Its strict-offline runtime identity is
`4c89ca10c3adaae0a623461b245d1dfc2ee53329e7b083927426961149ca583f`.

The runtime recreated four deterministic complete 640x480 RGB PNGs, selected
frame one for top and wrist, decoded exact RGB bytes, selected calibrated
`q_after`, and ran the actual cached checkpoint preprocessor and tokenizer on
CPU. It recorded the 640x480 preprocessor tensors, normalized state, 200-token
IDs and mask, exact prompt, two real 224x224 images, the missing right-wrist
`-1` image, and masks `[true, true, false]`. The future model call is pinned to
`images`, `img_masks`, `tokens`, and `masks`; state is represented in prompt
tokens and is not a separate model argument.

The normalized fixture state is
`[-0.1331068873, 0.0956475958, -0.1740649343, -4.7774586678,
0.9459711909, 1.1012960672]`. Wrist-flex and gripper therefore fall outside
the tokenizer step's declared `[-1, 1]` domain, and the exact discretized state
is `[110, 140, 105, -1, 249, 255]`. The artifact records this explicitly and
withholds `policy_shadow_input_valid`.

The first development execution was rejected before artifact creation when a
late offline-flag ordering caused a Hub metadata attempt; the socket interlock
blocked the connection. The corrected runtime establishes offline flags before
Transformers import and reports zero network attempts. No model was
instantiated, no model weight was named or read, and no inference,
postprocessing, policy shadow, MuJoCo replay, hardware enumeration/open,
serial/camera/Studio access, reconnect, register write, torque change, motion,
optimizer, training, paid compute, or destructive action occurred.

Thirty direct adversarial tests pass; the focused gate is 153 tests in both
`.mujoco_venv` and the pinned LeLab runtime. The exact runner reproduces the
artifact, source and gate writers verify in both runtimes, compilation and
privacy/path/diff checks pass, and the 352-test broad offline gate passes in
82.674 seconds. Reviewer decision 084 accepts only
`fixture_pi05_model_ready_tensor_parity_conformant` and keeps the live gate and
`training_lock` closed.
