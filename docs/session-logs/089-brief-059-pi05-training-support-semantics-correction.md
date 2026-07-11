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
