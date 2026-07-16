# Brief 208 - T20.36o Bounded X Episode-0 Bridge Design

## Status

Active model-free design/authority slice under the owner's 2026-07-16
continuation and priority-3 direction. T20.36n is verified mixed-negative by
Reviewer 266. Gate C route is open; Gate C execution remains closed.

**Manager review correction resolved (2026-07-16T03:08 CDT):** The first
preserved design used a minimum-across-phases envelope and is superseded by the
follow-up artifact `8294c63b...`. The effective design applies frozen amendment
`463477dc...` unchanged at each chunk: offsets `0..31 = reach`, offsets
`32..49 = grasp`, the exact signed phase/joint tables, and only the six
unexecuted terminal positions masked. Code, artifact reconstruction, and six
focused tests prove the correction without rewriting history.

## Objective

Freeze the exact episode-0 PI0.5 execution semantics, source windows, target
masks, deterministic probe identities, correction/replay schedule, finite
update ceiling, and pass/stop rules needed to make X eligible for a separately
authorized one-episode Gate C rollout. This boundary may inspect signed source
artifacts and cached dataset records but may not construct a model or optimizer.

## Frozen Execution Contract

- Use a new Gate C contract with `n_action_steps=50`; the T20.32 legacy
  `ACTION_HORIZON=5` adapter contract is explicitly ineligible.
- Reset `PI05Policy`'s action queue exactly once immediately before the
  244-frame rollout. `select_action` may sample only when that queue is empty
  and then executes one queued action per environment frame.
- The only chunk-start frames are `[0, 50, 100, 150, 200]`.
- The corresponding executed lengths are `[50, 50, 50, 50, 44]`.
- Bind each start to its exact episode-0 source frame identity, phase, state,
  images, task, and 50-step target window before any optimizer creation.
- At start 200, target and acceptance masks contain 44 true and six false
  positions. The six unexecuted tail predictions are excluded from loss
  acceptance, amended-gate decisions, and actor-valid evidence; they remain
  reportable only as non-executed diagnostics.
- Bind five deterministic probe seeds per start before training. No
  post-result seed substitution is allowed.

## Bridge Design Requirements

1. Mechanically derive the five starts and masks from rollout length 244 and
   queue size 50; reject conflicting horizon, reset, padding, or cadence data.
2. Record the local `PI05Policy.select_action` source revision and file hash
   that establish queue-empty sampling and one-action popping.
3. Freeze the exact five observation/target records and their byte/content
   identities. Missing frame, phase, image, state, target, or mask evidence
   fails closed.
4. Extend X's physical-Jacobian/time-weighted correction only across these
   five bound states. Preserve paired standard replay so a bridge cannot trade
   source-batch competence for downstream chunk-start competence.
5. Derive the finite correction set as five starts by five probe seeds by ten
   denoise steps (`250` examples) and pre-register deterministic ordering,
   source-replay ratio, update ceiling, mid-run probes, selection rule, and
   first-complete-pass stop before optimizer creation.
6. Frozen amendment `463477dc...` must pass at every executed joint/timestep
   for every registered probe at all five starts. The original uniform metric
   remains reported but non-gating. Any non-finite value, source-replay
   regression, identity drift, or unmasked tail use fails closed.
7. A pass grants no Gate C execution by itself. It only permits a separate
   central request, preflight, one-episode permit, reviewer decision, and
   remote-preserved boundary.

## Required Deliverables

- Deterministic execution/window spec generator and exact verifier.
- Tests for starts, lengths, queue-reset count, horizon rejection, final-tail
  mask, source identities, probe uniqueness, and failure on stale or missing
  evidence.
- Model-free update-budget/replay critique with one frozen selection rule.
- Central baseline-inference authority request and preflight in a later
  separately reviewed boundary; no model or optimizer action in this slice.

## Baseline-First Route

Before any optimizer creation, load X once under a separate one-use permit and
capture both decoded chunks and complete denoise paths for the five bound
states, five registered seeds, and two exact repeats. If update 0 passes every
executed cell, skip optimization and request separate Gate C authority. If it
fails, retain the 250 exact correction trajectories, close the inference
permit, and compose a separate training specification and permit from those
artifacts. This prevents a 2,500-update run when X already covers the real
chunk-start states and prevents optimizer authority from being inferred from
an observation-only probe.

## Prohibited Actions

No model construction/load/inference, optimizer creation/training, checkpoint
mutation, Gate C rollout, threshold change, candidate substitution, physical
hardware, network/download, external compute, or Brev.

## Verified Design Boundary

Artifact `8294c63b...` binds policy source `b05b6afe...`, LeRobot revision
`e40b58a8...`, exact episode-0 observations and targets, phase runs, starts
`[0,50,100,150,200]`, lengths `[50,50,50,50,44]`, and final mask
`44 true + 6 false`. It preserves amendment `463477dc...` exactly with
per-chunk offsets `0..31 = reach` and `32..49 = grasp`; it neither weakens nor
tightens the signed gate. The bounded fallback preserves X's ten uses per correction
example: 250 examples, 2,500 updates maximum, unchanged `2.5e-5` LR, 1:1
unique standard replay, probes at 0/500/1000/1500/2000/2500, and first
confirmed pass selection. Six focused tests and the exact verifier pass.
Reviewer 267 verifies corrected design `8294c63b...` and permits only
implementation of the separate baseline-inference authority boundary next.

The baseline authority/preflight/permit implementation now passes 25 combined
focused/design/pointer tests. Reviewer 268 verifies implementation only and
requires it to be committed, pushed, and origin-confirmed before the
materializer may hash the checkpoint/base snapshot and emit authority files.
No baseline authority artifact, marker, checkpoint tensor read, model action,
or optimizer action exists at this boundary.

## Verified Pre-Run Boundary

Implementation `467ad92` is on origin. Owner grant `e3d80dcd...`, central
decision `e649d3dc...`, live preflight `f0794abd...`, and one-use permit
`3d6a1548...` reconstruct exactly. The permit binds 50 decoded chunks, 500
denoise-step records, the five start-zero hashes, base-noise checks before each
decode, and marker-first tensor access. Reviewer 269 authorizes the sole
baseline attempt only after this boundary is committed, pushed, and confirmed
on origin. No marker or model action exists yet.

## Verified Runner Boundary

The one-use runner now binds exact live observation/target checks, source RNG
initialization, noise-before-decode verification, start-zero-first hash gating,
50 decoded chunks, 500 complete denoise records, frozen masked scoring, and
fail-closed retained results. Denoise matrices use signed base64 float32
little-endian payloads with exact shape and byte hashes so remote retention
does not discard any path value. Reviewer 270 verifies the complete runner
diff and requires commit/push/origin confirmation before the marker exists.
Implementation `781e0e0` is now preserved on origin; only this canonical
pointer boundary remains to be pushed and confirmed before execution.

## Verified Baseline Result

The sole attempt produced result `e6537428...`: all start-zero hashes and all
decoded/denoise repeats reproduce, while the frozen bridge fails at update 0.
Start 0 passes 3/5 seeds with the prior five small gripper misses; starts
50/100/150/200 pass 0/5 with 649/543/513/505 violations. The retained source
objective ratio still passes. Complete tensors and 500 denoise records are
tracked under receipt `1154d524...`, and the tracked-only verifier reconstructs
the result without the ignored run summary. Reviewer 271 routes only to a
separate bounded optimizer authority; no optimizer or Gate C authority exists.

## Verified Optimizer-Spec Implementation

The model-free compiler now decodes the retained float32 paths, reproduces
start-zero normalized target `b7c73491...`, constructs the frozen 250-example
manifest `1a7e3202...`, and rematerializes every derived-noise hash. The
prospective signed spec is `50e0569d...`. Reviewer 272 verifies implementation
only and requires commit/push/origin confirmation before the spec artifact is
written. No model or optimizer action exists.
