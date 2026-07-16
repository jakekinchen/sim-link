# Brief 198 - T20.36g Exact SmolVLA Gate B Entry Design

## Objective

Design and sign the smallest exact local SmolVLA Gate B entry contract from the
verified T20.36c cache/source inventory and T20.36f ACT localization, without
loading a model, reading checkpoint tensors, selecting a product policy, or
running an optimizer.

## Frozen Inputs

- T20.36c local policy-track preflight `61fcf124...` and exact LeRobot source
  head `e40b58a8...`.
- T20.36d canonical episode-0 horizon-50 batch, two camera features, six-joint
  order, T20.23 MEAN_STD state/action statistics, and unchanged Gate B.
- T20.36f localization `472e5ec5...`: exact ACT objective/hash reproduction,
  direct/queue equality, and normalized boundary/endpoint underfit.
- Existing local SmolVLA base/VLM cache metadata. No download is allowed.

## Required Design

1. Enumerate the exact SmolVLA source/config/processor/model files and local
   cache metadata without reading tensor content.
2. Resolve the cached three-camera processor expectation into an explicit
   two-camera configuration override bound to base and wrist features. No fake
   third image, alias, duplication, or silent camera drop is allowed.
3. Bind the canonical one-batch action/state/image hashes, dataset statistics,
   joint order, horizon 50, physical coordinate round trip, and task text.
4. Specify the smallest Mac-local trainable strategy supported by the pinned
   source, exact MPS/dtype/runtime preflight, optimizer/schedule/seed, one-use
   attempt marker, finite evidence, checkpoint format, and stop rule.
5. Keep the unchanged 0.10 objective ratio and 0.05-rad all-element physical
   maximum as Gate B. Report task-consequence metrics separately; do not gate
   on them or amend thresholds in this slice.
6. Bound results: a pass proves only SmolVLA one-batch capability and may route
   a separate Gate C design; a fail routes architecture/optimizer localization.
   Neither result selects SmolVLA as a product policy by claim.

## Acceptance

- The signed design is deterministic, source/cache/content bound, test covered,
  and remotely preserved.
- Any later model load, tensor read, inference, or optimizer requires a separate
  task-specific central decision and reviewed pre-run boundary.

## Prohibited Actions

Network/download, checkpoint tensor read, model load/construction, inference,
optimizer creation/training, ACT retry, policy selection, Gate B amendment,
Gate C, rollout, hardware, camera, serial, external compute, or Brev.
