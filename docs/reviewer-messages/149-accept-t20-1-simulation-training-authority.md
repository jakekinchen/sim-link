# Reviewer Decision 149 - Accept T20.1 Simulation-Only Training Authority

`CONTINUE`

Reviewed feature boundaries `603e087857d4a552fed346e0a5835d2da8cd7b21` and
`8c57c8ac8d53076b043848af885613eba1ae4261`.

The T20.1 writer reconstructs its two-train/one-held-out-episode tensor view
from append-only T17.5b evidence, verifies every selected raw-byte hash and
actor-safe input/action field, and fails on a conflicting materialized view.
The owner grant is an explicit prerequisite in the central authority contract,
is scoped to simulation-only training, binds the T20.1 spec, and has a finite
validity interval that the execution-time verifier enforces. Missing, altered,
stale, contradictory, expired, or unauthorized claims fail closed.

Independent recomposition grants only `simulation_training_ready`. Physical
transfer remains missing all five physical prerequisites, and promotion remains
missing evaluation, safety, provenance, and deployment prerequisites. No source
artifact claims global authority; no model, optimizer, hardware, external
compute, or Brev action ran in this slice.

Focused and broad data/authority regression gates passed. Open the
simulation-only training lock after this review/state boundary is remotely
preserved; start T20.2 separately.
