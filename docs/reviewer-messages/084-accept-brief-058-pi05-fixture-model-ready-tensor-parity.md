# Reviewer Decision 084 - Accept Brief 058 PI0.5 Fixture Model-Ready Tensor Parity

**Date:** 2026-07-11

## Decision

`CONTINUE T16.5C; ACCEPT BRIEF 058 FIXTURE MODEL-READY TENSOR PARITY; LIVE GATE CLOSED`

Implementation `77724e14ba499fadb981c4099b334a19a235c51d` is present on
`origin/codex/pi05-autolearn-loop`.

The implementation first reverifies the exact Brief 056 source contract and
the still-blocked Brief 057 reviewed-input gate. It then rebuilds the signed
static-pose fixture, substitutes four deterministic complete 640x480 RGB PNG
streams, binds the two signed camera identities bijectively to top/base and
wrist/left-wrist, selects the highest complete frame index, and selects the
calibrated six-joint `q_after` state in the declared units and order.

The pinned LeLab runtime loads only a temporary mirror containing the exact
checkpoint preprocessor JSON and normalizer state. Hugging Face offline flags
and a socket interlock are established before dependency import. The actual
rename, batch, normalizer, PI0.5 prompt, tokenizer, and CPU device steps run
against the exact cached tokenizer revision. The exact unbound
`PI05Policy._preprocess_images` method then produces two real 224x224 images
and one absent-right-wrist `-1` image with masks `[true, true, false]`. A
no-model shim supplies only a CPU device; no policy constructor or model call
runs.

The artifact records canonical tensor byte hashes, shapes, dtypes, ranges, the
full prompt and nonpadding token IDs, camera order, frame-byte and decoded-RGB
hashes, action representation, 50-step chunk/horizon, and the reset-before-
sample queue requirement. It also records that PI0.5 inference calls only
`images`, `img_masks`, `tokens`, and `masks`; the six-joint state is embedded in
the prompt tokens rather than passed as a separate model tensor.

The fixture exposed a real non-authorizing concern: normalized wrist-flex and
gripper values are outside the tokenizer step's declared `[-1, 1]` input
domain, producing discretized values `-1` and `255`. This does not invalidate
the parity proof, because the artifact truthfully captures the exact pinned
behavior, but it independently prevents any `policy_shadow_input_valid` claim.
Future live preprocessing must range-audit the real state before shadow
inference.

The first development execution attempted Hub template metadata because the
offline flags were initially set after Transformers import. The socket
interlock blocked the connection before access and no artifact was written.
The corrected implementation establishes offline mode before every Hugging
Face import; the accepted runtime reports zero network attempts and reproduces
the golden runtime identity.

The complete diff was reviewed for fixture-to-live relabeling, source or gate
substitution, camera ambiguity, PNG corruption, state order/unit/selection
drift, tokenizer and tensor substitution, missing-camera mask escalation,
action/horizon/queue drift, false model/weight/network/hardware claims, private
identity leakage, path aliasing, and authority escalation. The wrong Python
runtime fails before preprocessing. No absolute path, device identity, raw
camera identity, USB serial, or private evidence path is present.

One hundred fifty-three focused tests pass in each robotics runtime. All
source, gate, static-fixture, and tensor-parity writers/verifiers pass, and the
352-test offline authority/twin regression gate passes in 82.674 seconds.

Grant only `fixture_pi05_model_ready_tensor_parity_conformant`. Do not grant a
real reviewed-input bundle, accepted live policy input,
`static_pose_bracketed_observation`, `policy_shadow_input_valid`, policy
shadow, model construction or weight load, inference, postprocessing, MuJoCo
replay, hardware access, actuation, physical qualification or transfer,
promotion, or training authority.

The next decisive step is a fresh hardware-supervised `on-request` parent with
a finite window and a separately reviewed live-gate transition. This current
`never` parent must not access hardware or open the live gate.
