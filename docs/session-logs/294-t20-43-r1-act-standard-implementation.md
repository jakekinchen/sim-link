# Session Log 294 - T20.43 R1 ACT Standard Implementation

## Implementation

- Added signed, rebuildable contracts for the exact verified R0 source,
  standard full ACT recipe, model-free Gate A, task-specific owner/central
  authority, runtime preflight, one-use permit, immutable marker, and signed
  pre-run acceptance.
- Added a no-write live collector and exclusive six-artifact materializer. It
  binds the reviewed implementation commit, exact origin ancestry, scoped
  cleanliness, fixed package versions, MPS, disk, cached ResNet-18 bytes, and
  every output path absent and unaliased.
- Added the sole 10,000-update ACT runner using the full LeRobot defaults,
  official EpisodeAwareSampler, batch 8, AdamW `1e-5`/`1e-4`, no scheduler,
  and fixed checkpoints `[0,500,1000,2500,5000,7500,10000]`.
- Added rollout-primary evaluation at every checkpoint under chunk-50 and
  receding-10 semantics. Each variant resets once, masks unexecuted tails,
  retains complete 244-frame comparisons, first divergence, strict-v2/T20.38
  margins, frozen-amended/uniform report-only metrics, decode hashes, and a
  signed mirror MP4.
- Added deterministic first-Gate-C selection: earliest checkpoint first, then
  chunk-50 as the same-checkpoint tie-breaker. The run continues to 10,000
  finite updates and later evidence cannot replace the first pass.
- Extended the existing rollout-mirror renderer to accept only independently
  verified T20.43 traces.

## Evidence

- Spec `b3a510f8...` rebuilds exactly from R0 result `d238379b...`, mixture
  `37b30d34...`, statistics `02ba0e70...`, retained dataset manifest
  `bd36b7c4...`, frozen gate `463477dc...`, T20.38 receipt `042bf0be...`,
  LeRobot source `e40b58a...`, and cached ResNet bytes `f37072fd...`.
- A model-free Gate A probe passes with identity `90217d2b...`: 129 episodes,
  31,366 frames, exact package/compact statistics, zero manual normalization
  error, 3.8147e-6 float32 postprocessor inverse error, and 1.4211e-14
  coordinate round-trip error.
- Nine focused T20.43 tests and 75 focused-plus-broad authority, dataset,
  ACT closed-loop, strict-v2 receipt, consequence-gate, coordinate, R0, and
  project-pointer tests pass.
- The real-source Gate A/central/runtime/permit bundle reconstructs in memory.
  Ruff check, Ruff format, Python compilation, strict JSON, spec verification,
  and whitespace checks pass.

## Result

This is implementation evidence only. Gate A and live authority artifacts have
not been written. No attempt marker, cached backbone tensor read, model,
inference, optimizer, checkpoint, rollout, MP4, Gate C claim, hardware,
network, external compute, or Brev action occurred. Reviewer 291 may authorize
only origin-preserved Gate A/authority materialization and a separate pre-run
review.
