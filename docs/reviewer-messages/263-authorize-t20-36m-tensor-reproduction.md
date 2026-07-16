# Reviewer Decision 263 - Authorize T20.36m Tensor Reproduction

**Decision:** `AUTHORIZE_ONE_HASH_BOUND_INFERENCE_ATTEMPT`

## Reviewed Boundary

Brief 206; owner grant `155a7338...`; central request `0e0aec0d...`; central
decision `31eabbbd...`; preflight `970342fe...`; permit `374ad4f2...`;
implementation `52f15cc25b1122b8dadac1d336cb6fffeb527e65`; exact source result
`08ef923d...`; frozen gate `463477dc...`; frozen score `0f8ae393...`; 31
focused/source/pointer tests; exact T20.36j output verifier; checkpoint byte
tree; current branch/remote parity; and the complete scoped diff.

## Findings

- The central composer mechanically grants only `simulation_training_ready`;
  physical transfer and promotion remain withheld. The owner and permit narrow
  that generic state to model construction/load/inference only.
- The live environment reproduces the signed 57-package closure, LeRobot stack,
  canonical batch, MPS availability, and six-file checkpoint tree.
- The checkpoint is byte-hashed, but no tensor is deserialized and no model is
  constructed/loaded before the attempt marker.
- The permit allows exactly seeds 20260811-20260815, two repeats each, ten 50x6
  tensors, and frozen Gate B scoring. All five pre-existing hash pairs must
  match before scoring.
- Optimizer, training, new seeds, third repeats, threshold changes, Gate C,
  selection, hardware, network/download, external compute, and Brev are false.
- The first marker consumes the one-use permit even on runtime failure.

## Disposition

Authorize exactly one local-MPS T20.36m attempt after this authority/preflight
boundary is committed, pushed, and confirmed on origin. A hash mismatch fails
closed. A frozen Gate B pass only opens a separate Gate C authority request; a
failure closes the learned-policy Gate B branch.

## Withheld Authority

No optimizer/training, checkpoint mutation, new seed, extra repeat, threshold
change, Gate C execution, policy selection/promotion, hardware, network,
external compute, or Brev.
