# Reviewer Decision 269 - Authorize T20.36o X Baseline Capture

**Decision:** `AUTHORIZE_ONE_X_FIVE_STATE_BASELINE_CAPTURE`

## Reviewed Boundary

Brief 208; corrected bridge design `8294c63b...`; Reviewers 267-268;
implementation `467ad92786be7c65e3bfa0ba95a6980473643b25` on origin; owner grant
`e3d80dcd...`; central request `1520ee88...`; central decision `e649d3dc...`;
runtime preflight `f0794abd...`; one-use permit `3d6a1548...`; exact X
checkpoint `40c94f66...`; frozen-base snapshot tree `55544131...`; 25
focused/design/pointer tests; exact materializer verification; branch/remote
parity; absence of every attempt/result path; and the complete scoped diff.

## Findings

- The corrected design applies frozen amendment `463477dc...` unchanged at
  every chunk and masks only the six unexecuted terminal positions.
- The central composer grants only generic `simulation_training_ready`; the
  owner grant and permit narrow it to one construction/load and the exact
  baseline capture.
- Live Python 3.12/MPS and datasets 4.8.5, LeRobot 0.6.1, PyArrow 25.0.0,
  safetensors 0.8.0, torch 2.11.0, and Transformers 5.5.4 match.
- The preflight byte-hashes the 2.77 GB trainable checkpoint and exact
  four-file frozen-base snapshot without deserializing a tensor. Current and
  origin commits both equal `467ad92...`.
- The permit allows only starts 0/50/100/150/200, lengths 50/50/50/50/44,
  seeds 20260721-20260725, two repeats, 50 decoded chunks, and 500 denoise-step
  records. Every base-noise hash must match before decode.
- Start 0 must reproduce the five retained X action hashes before new-state
  evidence is accepted. All five target/mask/observation bindings are exact.
- A marker must precede checkpoint tensor read and model construction. The
  first marker consumes the permit even on failure.
- Optimizer, training, retry, Gate C, threshold change, hardware, network,
  external compute, and Brev remain false.
- No marker, checkpoint tensor read, model action, output tensor, trajectory,
  result, or failure result exists at review time.

## Disposition

Authorize exactly one local-MPS baseline capture after this complete authority
boundary is committed, pushed, and confirmed on origin. A start-zero hash,
base-noise, repeat, target, mask, source, or runtime mismatch fails closed. A
complete pass only routes to a separate Gate C authority request; a failure
may retain correction trajectories but grants no optimizer authority.

## Withheld Authority

No second attempt, optimizer/training, Gate C execution, threshold change,
policy selection/promotion, hardware, network, external compute, or Brev.
