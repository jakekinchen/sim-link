# Reviewer Decision 268 - Verify Corrected T20.36o Design and Authority Implementation

**Decision:** `VERIFY_EXACT_FROZEN_GATE_BRIDGE_AND_AUTHORITY_IMPLEMENTATION`

## Reviewed Boundary

Brief 208; corrected bridge design `8294c63b...`; Reviewer 267; baseline central-authority
composer, runtime-preflight, permit, and marker implementations; materializer;
seven authority/permit tests; six design tests; twelve pointer tests; current
branch/remote parity; absence of all baseline authority/output artifacts; and
the complete scoped diff.

## Findings

- The first design `b44bd55b...` is ineligible because its
  minimum-across-phases envelope tightened signed reach thresholds. Corrected
  design `8294c63b...` preserves amendment `463477dc...` exactly at every
  chunk (`0..31=reach`, `32..49=grasp`) and masks only six unexecuted terminal
  positions. Reviewer 267 records the correction and preserves the historical
  artifact as superseded and ineligible.
- The owner grant narrows execution to one X construction/load and exactly
  five starts by five seeds by two repeats: 50 decoded chunks and 500 denoise
  step records.
- The central composer may grant only generic `simulation_training_ready`;
  optimizer, training, Gate C, hardware, network, external compute, and Brev
  remain false in the owner grant and finite permit.
- Preflight requires Python 3.12, MPS, exact dependency versions, exact X
  trainable checkpoint bytes, exact four-file frozen-base snapshot, at least 2
  GiB free, branch/remote equality, and no existing attempt or result.
- The permit binds the five starts, lengths, source observation/target/mask
  identities, five fixed seeds, base-noise hashes, two repeats, source
  construction seed, and the five signed start-zero action hashes.
- A marker must exist before checkpoint tensor deserialization, model
  construction, load, or inference. It cannot authorize an optimizer.
- Materialization itself performs no checkpoint tensor read or model action;
  it byte-hashes the checkpoint and snapshot and writes only authority,
  preflight, and permit artifacts.
- No authority/preflight/permit, marker, model, inference, optimizer, Gate C,
  hardware, network, external compute, or Brev action has occurred yet.

## Disposition

Verify corrected design `8294c63b...` and the authority implementation. Commit
and push this complete boundary, confirm origin, then run the
materializer under the exact external/lerobot Python 3.12 environment. Review
the resulting authority, live preflight, and permit as a separate boundary
before any marker or checkpoint tensor read.

## Withheld Authority

No materialization before remote preservation; no attempt marker, checkpoint
tensor read, model construction/load/inference, optimizer/training, Gate C,
hardware, network, external compute, or Brev.
