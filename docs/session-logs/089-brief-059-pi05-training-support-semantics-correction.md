# Session 089 - Brief 059 PI0.5 Training-Support Semantics Correction

**Date:** 2026-07-11

Brief 059 began offline at `2026-07-11T17:13:11-05:00` from remotely matched
HEAD `7f8347a8eb69b75dd36ad04d14a3b57720785fb4`. Branch, upstream, and
`origin/codex/pi05-autolearn-loop` matched exactly. All unrelated modified and
untracked paths remain outside this slice.

Read-only diagnosis used only the already pinned checkpoint config,
preprocessor, normalizer statistics, calibration profile, fixture artifact,
and local LeRobot source. It did not name or read model weights, instantiate a
model, infer, access hardware, replay, train, or use paid compute.

The checkpoint and model card both explicitly preserve `STATE/ACTION =
MEAN_STD`, while the PI0.5 source default is `QUANTILES`. The serialized
checkpoint wins because it is the path used during training and inference.
The tokenizer step's `[-1, 1]` bins therefore act as a textual discretizer with
saturation, not as a universal hard-validity domain.

The fixture wrist-flex value `-5.054945...` is below the checkpoint training
minimum `20.239624...`, q01 `40.861965...`, and mean-minus-std
`48.049858...`. The fixture gripper value `50.0` is above mean-plus-std
`47.734813...` but inside q01-q99 `[1.465412..., 59.614234...]` and observed
min-max `[0.779220..., 79.935066...]`. Brief 058's conclusion that both joints
were independently invalid was therefore too broad. Brief 059 will correct the
machine artifact and canonical interpretation without altering trained
preprocessing bytes.

Implementation `f6b6c08299ddc9a460e6ec5c711fd0783cd2356a` is present on
`origin/codex/pi05-autolearn-loop`. The corrected artifact remains at
`configurations/robot_lab/pi05_fixture_model_ready_tensor_parity.json` with
schema `scenesmith.pi05_fixture_model_ready_tensor_parity.v2`, identity
`b20e078242af31227c6d77bedc08bd8d54a1be2df5540a8e5140b30a3e2bf25e`,
and runtime identity
`1642f75c3801df58a7978b3e1d6c0a255641388b11a338f3bc2987fdb584f21a`.

The runtime audit binds the existing normalizer file
`8dc4c304b136dc66eca1b3156059b3d2bbd296864fff99e8453ed5fc128d070f`
and all nine six-wide statistic vectors. It recomputes mean/std normalization,
exact `numpy.digitize(...)-1` bins, q01-q99 membership, observed min-max
membership, and ordered joint classifications. The fixed bin reference
interval is explicitly not a hard input-validity domain, and neither clipping
nor a normalization-mode mutation is allowed.

The corrected summary lists wrist-flex and gripper outside mean±std,
wrist-flex alone outside q01-q99 and observed min-max, and shoulder-pan,
shoulder-lift, elbow-flex, wrist-roll, and gripper within observed support.
Future no-actuation shadow analysis may record an out-of-support state only
after independent live-input acceptance; policy actuation from such a proposal
remains blocked.

The pure support logic was split from the execution module. Fifteen direct
support tests and thirty-seven fixture-parity tests pass. The focused gate is
175 tests in each robotics runtime, all exact writers/verifiers pass, and the
374-test broad offline authority/twin gate passes in 86.332 seconds. Exact
comparison with implementation `77724e1` proves every model-facing tensor,
mask, prompt, token, selected frame, state, and action/queue contract is
unchanged.

No model was instantiated, no model weight was named or read, and no inference,
postprocessing, policy shadow, MuJoCo replay, hardware enumeration/open,
serial/camera/Studio access, reconnect, register write, torque change, motion,
optimizer, training, paid compute, destructive action, or unrelated dirty path
was touched. Reviewer Decision 085 supersedes only the range interpretation in
Decision 084 and grants only
`fixture_pi05_training_support_audit_conformant`; the live gate and
`training_lock` stay closed.
