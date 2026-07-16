# Reviewer Decision 276 - Authorize T20.36o Bounded Optimizer Attempt

**Decision:** `VERIFY_RUNNER_AUTHORIZE_ONE_BOUNDED_OPTIMIZER_ATTEMPT`

## Reviewed Boundary

Brief 208; optimizer spec `50e0569d...`; permit `f9bad1ae...`; runner
implementation `9f3538e` on origin; the complete runner/probe/result/checkpoint
diff; 36 combined T20.35c/T20.35x/T20.36o tests; Python compilation; exact
five-window and 250-example model-free rematerialization; and the successful
non-consuming live preflight.

## Findings

- The runner verifies branch/origin preservation and creates both immutable
  attempt markers before checkpoint tensor deserialization, model
  construction, or optimizer creation.
- The live correction objective binds all five start states, masks only the
  six non-executed positions at start 200, divides by executed positions times
  32 dimensions, and applies the frozen physical-joint and time weights.
- Every update is paired with the unique permit-bound start-zero standard
  replay seed. AdamW parameters, the 1.0 gradient clip, the 2,500-update
  ceiling, and the five 500-update probes reconstruct from spec
  `50e0569d...`.
- Every probe verifies the registered base-noise hash before decode, captures
  five starts by five seeds by two repeats, requires bit-identical repeats,
  scores only executed cells under amendment `463477dc...`, and checks the
  unchanged source-objective ratio.
- The first complete confirmed pass stops training; otherwise the sole run
  stops at 2,500 updates. Either route writes the full tracked probe tensors,
  a signed result, and the selected/final local checkpoint. No retry exists.
- The exact preflight returned permit `f9bad1ae...` and spec `50e0569d...` and
  left the run root, tracked marker, probe, result, failure, and checkpoint
  paths absent. The duplicate `cv2`/`av` Objective-C class warning was
  non-fatal; no camera or hardware object was opened.
- Gate C, threshold change, hardware, network/download, external compute, and
  Brev remain closed.

## Disposition

Authorize exactly one permit-bound local-MPS optimizer attempt after this
review boundary is committed, pushed, and confirmed on
`origin/codex/pi05-autolearn-loop`. The attempt must stop at its first complete
confirmed pass or at update 2,500, retain its full signed evidence, and receive
a separate result review. A passing bridge may only request separate Gate C
authority; it does not authorize Gate C execution.

## Withheld Authority

No second attempt or retry; no threshold change, Gate C execution, policy
selection, physical actuation, camera/serial access, network/download,
external compute, Brev, physical transfer, promotion, or destructive action.
