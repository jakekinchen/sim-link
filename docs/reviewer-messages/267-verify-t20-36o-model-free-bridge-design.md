# Reviewer Decision 267 - Verify T20.36o Model-Free Bridge Design

**Decision:** `VERIFY_MODEL_FREE_BRIDGE_DESIGN_ROUTE_BASELINE_CAPTURE_AUTHORITY`

## Reviewed Boundary

Brief 208; owner priority-3 direction; Reviewer 266; frozen amendment
`463477dc...`; T20.36n result `f8d7866e...`; X checkpoint `40c94f66...`;
PI0.5 source `b05b6afe...` at LeRobot revision `e40b58a8...`; episode-0 raw
rollout `9e186088...` and source bytes `586a3e67...`; dataset parquet
`7843e531...`; corrected bridge design `8294c63b...`; exact generator/verifier; six
focused tests; project-pointer tests; branch/remote parity; and the complete
scoped diff.

## Findings

- `PI05Policy.reset` recreates the queue at `n_action_steps`, and
  `select_action` samples only when empty, slices that many actions, and pops
  one action per call. The exact source file and both function identities are
  bound.
- One reset over 244 frames at 50 actions yields exactly starts
  0/50/100/150/200 and executed lengths 50/50/50/50/44. The contract rejects
  legacy horizon 5.
- All five source observations bind raw state/velocity, encoded image hashes,
  dataset state, dataset image hashes, and pixel equivalence. Dataset PNGs are
  re-encoded but pixel-identical to source; neither byte lineage is hidden.
- All 244 executed source actions, frame IDs, record identities, and phase runs
  are retained. The final six values repeat the last source action only for
  tensor shape and are false for loss, gate, and actor evidence.
- Manager review found that the first preserved minimum-across-phases envelope
  silently tightened two reach thresholds. The corrected artifact applies
  amendment `463477dc...` unchanged at every chunk: offsets 0-31 use the
  signed reach table, offsets 32-49 use the signed grasp table, and only the
  six unexecuted terminal positions are masked. The earlier artifact remains
  history but is superseded and cannot authorize baseline capture.
- The update-0 baseline probe precedes optimizer creation. A complete pass
  skips training. A failure retains 250 current-path correction trajectories
  before a separately reviewed training request.
- The fallback ceiling of 2,500 updates follows mechanically from five starts
  by five seeds by ten denoise steps by ten uses per example. It preserves X's
  LR, physical/time weights, 1:1 unique standard replay, deterministic order,
  five mid-run probes, first confirmed pass selection, and no retry.
- No checkpoint tensor read, model construction/load/inference, optimizer,
  Gate C, threshold change, hardware, network, external compute, or Brev action
  occurred.

## Disposition

Verify the model-free design artifact. Continue T20.36o by implementing a
fresh central inference request, live preflight, and one-use permit for one X
load and the exact five-state/five-seed/two-repeat baseline plus trajectory
capture. Do not create an attempt marker or read a checkpoint tensor until that
complete boundary is committed, pushed, origin-confirmed, and separately
reviewed.

## Withheld Authority

No attempt marker, checkpoint tensor read, model construction/load/inference,
optimizer/training, Gate C execution, threshold change, policy selection,
hardware, network, external compute, or Brev.
