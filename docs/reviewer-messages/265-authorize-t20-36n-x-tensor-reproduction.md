# Reviewer Decision 265 - Authorize T20.36n X Tensor Reproduction

**Decision:** `AUTHORIZE_ONE_HASH_BOUND_T20_35X_INFERENCE_ATTEMPT`

## Reviewed Boundary

Brief 207; owner priority directive; source T20.35x spec `96efc6d3...`, run
`b5cc16ef...`, result `e79dacff...`, checkpoint `40c94f66...`; frozen gate
`463477dc...`; implementations `69a2f46`, `1aab35f`, and `a77a829`; owner grant
`a2b45382...`; central request `210d804e...`; central decision `5b40131b...`;
runtime preflight `8e99f9ad...`; one-use permit `2c6a1e78...`; MPS and exact
dependency map; 30 focused/current/pointer tests; exact T20.36m retention
verifier; remote parity; and the complete scoped diff.

## Findings

- Retained X evidence contains five hashes and aggregate errors, but no 50x6
  decoded tensor, so model-free amended-gate scoring is impossible.
- The live environment differed from the exact source runtime only at PyArrow
  24 versus 25. One cache-only, network-disabled restore installed the exact
  source-required `25.0.0`; the preflight binds all six dependency versions.
- The source checkpoint tree byte-hashes exactly. No checkpoint tensor was
  deserialized and no model was constructed, loaded, or run before review.
- Frozen base weights are independently bound to revision `7de66397...` and
  exact four-file tree `55544131...`, including model hash `0eb11ca9...`.
- The runner resets torch, NumPy, and Python RNGs to source seed 20260718
  immediately before construction and rejects every base-noise hash before
  `predict_action_chunk`, so a cache/construction/noise drift cannot hide as a
  consumed final-action mismatch.
- The permit allows only seeds 20260721-20260725, two repeats each, ten 50x6
  tensors, the five existing signed hashes, and frozen gate `463477dc...`.
- The tensor artifact path is tracked configuration evidence, and the result
  embeds the target plus a fresh-checkout rescore contract.
- T20.36m's existing exact tensor bytes are now remotely preserved unchanged;
  receipt `6a30749b...` independently reproduces all 162 recorded violations
  without model reconstruction or inference.
- Optimizer, training, new seeds, extra repeats, threshold changes, Gate C,
  selection, hardware, network, external compute, and Brev remain false.

## Disposition

Authorize exactly one local-MPS T20.36n attempt after this complete boundary is
committed, pushed, and confirmed on origin. The first marker consumes the
permit even on failure. A hash mismatch fails closed. An amended-gate pass only
routes to a separate Gate C bridge authority request.

## Withheld Authority

No retry, optimizer/training, new seed, extra repeat, threshold change, Gate C
execution, policy selection/promotion, hardware, network, external compute, or
Brev.
