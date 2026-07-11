# Reviewer Decision 082 - Accept Brief 056 PI0.5 Preprocessing Source Contract

**Date:** 2026-07-11

## Decision

`CONTINUE T16.5C; ACCEPT BRIEF 056 PI0.5 PREPROCESSING SOURCE CONTRACT; LIVE GATE CLOSED`

Implementation `fd4982097961d8df34435e2db5fd7c4397f050d4` is present on
`origin/codex/pi05-autolearn-loop`.

The fixture-only contract binds the signed robotics dependency lock and exact
PI0.5 executable source files, the cached checkpoint processor snapshot at
revision `84b551af1303e92d97d6752d43cc3c9f1a090778`, and the cached PaliGemma
tokenizer snapshot at revision `35e4f46485b4d07967e7e9935bc3786aad50687c`.
Cache refs, snapshot directories, contained blob symlinks, source files, and
parsed JSON are rehashed and reverified. The model-weight file is neither named
in the artifact nor opened by the implementation.

The bounded standard-library safetensors parser validates every tensor's type,
shape, offset, non-overlap, and complete file coverage, then reads only the
required six-wide state/action count, mean, and standard-deviation vectors. It
records 94,568 samples without embedding values and rejects malformed, aliased,
non-finite, boolean, fractional-count, nonpositive, overlapping, gapped, or
wrong-width evidence.

The contract also pins processor order, three 224x224 model image features, six
action outputs, 50-action chunks, MEAN_STD state/action normalization, the exact
six-joint order and units, the source CUDA device, and one derived CPU-only
preprocessing override. The prompt template includes the executable source's
real newline. No processor, tokenizer, model, policy input, or inference object
is constructed.

Production issuance remains mechanically blocked. The accepted live-session
review decision is absent, the two stable physical camera identities have no
reviewed top/wrist role assignment, and no task prompt has been reviewed. The
artifact has no proof labels and explicitly records that preprocessing, policy
shadow, inference, MuJoCo replay, hardware access, and follower commands did not
occur.

The complete diff was reviewed for authority escalation, source substitution,
fixture/live relabeling, cache and repository path aliasing, malformed numeric
evidence, model-weight access, absolute-path leakage, unsafe device defaults,
nondeterminism, and documentation drift. One hundred fourteen focused tests
pass in each robotics runtime. All relevant offline source and artifact
verifiers pass in both runtimes, and the 313-test regression gate passes in
70.328 seconds.

Grant only `pi05_policy_input_preprocessing_source_contract_conformant`. Do not
grant an accepted live policy input, `static_pose_bracketed_observation`,
`policy_shadow_input_valid`, policy shadow, model-weight load, inference,
actuation, physical qualification or transfer, promotion, or training
authority.

Next define a separate fixture-only reviewed-input issuance gate for the future
live-session acceptance decision, stable-camera role binding, and exact task
prompt. Do not fabricate any of those missing inputs, preprocess a live
observation, load weights, run inference, or reopen the live gate in this
thread.
