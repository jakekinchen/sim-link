# Reviewer Decision 270 - Verify T20.36o Baseline Capture Runner

**Decision:** `VERIFY_PERMIT_BOUND_X_BASELINE_CAPTURE_RUNNER`

## Reviewed Boundary

Brief 208; corrected bridge design `8294c63b...`; pre-run Reviewer 269;
permit `3d6a1548...`; the complete baseline artifact/scoring implementation;
the one-use runner; six focused contract tests; 27 combined
authority/contract/design/pointer tests; exact authority materializer
verification; live non-model loading of all five signed dataset observations;
and the complete scoped diff.

## Findings

- The runner is fixed to `n_action_steps=50`, starts 0/50/100/150/200,
  lengths 50/50/50/50/44, construction seed 20260718, five registered
  inference seeds, two repeats, ten denoise steps, and one X load.
- The attempt marker is written to both ignored and tracked paths before any
  checkpoint tensor deserialization or model construction. The runner refuses
  an existing marker, tensor, trajectory, result, failure result, or run root.
- The exact frozen snapshot tree, local stack, branch, HEAD/origin parity, and
  permit ancestor are rechecked before the marker. Runtime network access is
  disabled.
- Every base-noise hash is checked before its decode. Start 0 executes first;
  all five retained X hashes and both decoded/denoise repeats must match before
  a later start is accepted.
- Full 50x6 decoded tensors are retained as signed numeric JSON. All 500
  denoise records retain exact float32 state and velocity bytes as signed
  base64 little-endian payloads with shape and per-matrix hashes, avoiding
  remote file-size loss without discarding a value.
- Scoring preserves frozen amendment `463477dc...` exactly: relative offsets
  0-31 use reach thresholds, 32-49 use grasp thresholds, and only the final six
  unexecuted positions are excluded. The retained source objective ratio is
  still part of the conjunction; the uniform metric remains report-only.
- The live dataset-only preflight reproduced all five observations, camera
  pixel hashes, targets, and masks without creating a model or marker.
- An invalid proposed comparison to a nonexistent source
  `all_parameter_names` field was removed before execution. The signed
  trainable manifest and frozen PaliGemma boundary remain enforced.
- Optimizer/training, retry, Gate C execution, threshold change, hardware,
  network, external compute, and Brev are absent and fail closed.
- No marker, checkpoint tensor read, model action, tensor artifact, trajectory
  artifact, result, or failure result exists at review time.

## Disposition

Verify the implementation. Commit, push, and origin-confirm this complete
runner boundary before consuming permit `3d6a1548...`. After remote
preservation, Reviewer 269's one-attempt authorization may be exercised once.

## Withheld Authority

No second attempt, optimizer/training, Gate C execution, threshold change,
policy selection/promotion, hardware, network, external compute, or Brev.
