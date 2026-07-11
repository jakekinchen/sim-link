# Reviewer Decision 085 - Accept Brief 059 PI0.5 Training-Support Semantics Correction

**Date:** 2026-07-11

## Decision

`CONTINUE T16.5C; ACCEPT BRIEF 059 TRAINING-SUPPORT CORRECTION; SUPERSEDE BRIEF 058 RANGE INTERPRETATION; LIVE GATE CLOSED`

Implementation `f6b6c08299ddc9a460e6ec5c711fd0783cd2356a` is present on
`origin/codex/pi05-autolearn-loop`.

Brief 058 correctly captured the exact processor, tokenizer, prompt, and
model-input tensor bytes, but Reviewer Decision 084 incorrectly treated the
PI0.5 discretizer's `[-1, 1]` reference interval as a hard input-validity
domain. Brief 059 corrects that interpretation without altering execution.

The serialized checkpoint config and preprocessor both explicitly use
`STATE/ACTION = MEAN_STD`. That configuration was used for training and remains
the exact inference path; the source-code default of `QUANTILES` does not
override a serialized checkpoint. For this checkpoint, `np.digitize` maps the
mean/std-normalized state into fixed textual bins and saturates below/above the
reference interval. Values beyond one standard deviation are therefore not by
themselves absent from training support.

The v2 artifact binds all six `min`, `q01`, `q10`, `q50`, `q90`, `q99`, `max`,
`mean`, and `std` vectors plus the sample count and normalizer-file identity. It
independently recomputes normalization, exact discretized bins, quantile order,
per-joint support classes, and aggregate summaries.

The corrected fixture result is:

- Wrist-flex `-5.054945...°` is below observed training minimum
  `20.239624...°` and q01 `40.861965...°`, so it is outside observed training
  min-max support.
- Gripper `50%` is above mean-plus-std `47.734813...%`, but remains inside
  q01-q99 `[1.465412..., 59.614234...]%` and observed min-max
  `[0.779220..., 79.935066...]%`; it is not outside training support.
- The other four joints are inside q01-q99.

No clamp, normalization-mode switch, new binning, prompt edit, tokenizer edit,
or tensor edit was applied. A comparison against Brief 058 implementation
`77724e1` confirms exact equality for the fixture input, selected frames,
prompt text/hash, discretized state, raw state, all preprocessor tensors,
tokenizer outputs, three model-image tensors/masks, model-call contract, action
contract, and decoded-frame evidence.

The support audit permits only future no-actuation shadow analysis after all
independent real-input acceptance gates. It blocks using an out-of-support
proposal for policy actuation. It does not itself grant a real policy input or
shadow label.

The complete diff was reviewed for serialized/source normalization confusion,
silent quantile substitution, clipping, malformed or unordered statistics,
non-finite or nonpositive values, wrong joint order, incorrect exact bins,
normalizer-file substitution, wrist false acceptance, gripper false rejection,
fixture-to-live relabeling, and authority escalation. The new support module is
pure Python and contains no hardware, network, model, inference, replay,
optimizer, paid-compute, deletion, credential, or private-identity path.

One hundred seventy-five focused tests pass in each robotics runtime. The
exact v2 writer and the Brief 056/057 source gates reproduce, compilation and
privacy/diff checks pass, and the 374-test broad offline authority/twin gate
passes in 86.332 seconds.

Grant only the existing fixture tensor-parity capability plus the new local
`fixture_pi05_training_support_audit_conformant` capability. Do not grant a
real reviewed input, `static_pose_bracketed_observation`,
`policy_shadow_input_valid`, policy shadow, model construction or weight load,
inference, postprocessing, replay, hardware access, actuation, physical
qualification or transfer, promotion, or training authority.

The next real experiment still requires a fresh hardware-supervised
`on-request` parent, finite window, separate reviewed live-gate transition,
fresh owner-presence lease, discovery, and all-alias zero-holder proof.
