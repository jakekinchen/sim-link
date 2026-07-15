# Robo Scan And Sim-Link Integration Roadmap

## Decision

Do not merge the Git repositories or import Robo Scan's private implementation
into sim-link. Merge the product pipeline through immutable, versioned,
independently validated artifacts:

```text
Robo Scan
  capture -> calibrate -> reconstruct -> seal workcell export
                                      |
                                      v
                         immutable export receipt
                                      |
                                      v
Sim-link
  validate -> quarantine/admit -> compile MuJoCo twin candidate
           -> generate episodes -> train/evaluate policy -> compose authority
```

This gives the project one coherent foundry while preserving the release,
dependency, privacy, and safety boundaries that make the two repositories
useful.

## Source Of Truth

This roadmap owns cross-repository sequencing and deduplication decisions. It
does not own either repository's live status.

- Robo Scan's `GOAL.md`, active brief, and
  `docs/autonomous-workflow/project_state.json` own producer status.
- Sim-link's [`GOAL.md`](../GOAL.md),
  [`project_state.json`](./autonomous-workflow/project_state.json), and active
  ledger own consumer/training/authority status.
- The [Robo Scan integration boundary](./robo-scan-integration.md) owns the
  permanent handoff safety rules.

The producer handshake is no longer pending. Robo Scan Brief 054 is committed,
reviewer-accepted, and pinned at
`72eb02efe7e69981a5afab41a2733cd31ec03d4e`. Sim-link independently completed
I2 and the reference-only I3 descriptor at `67daad9`, `cb4e5a0`, and `d01416b`.
Those boundaries admit only labelled visual context. The next cross-repository
dependency is a real metric I4 bundle after Robo Scan M1-M4; until then each
repository continues its own local queue.

## Final Repository Ownership

| Capability | Robo Scan | Sim-link | Shared boundary / other runtime |
| --- | --- | --- | --- |
| Camera discovery, RGB-D capture, scan motion, frame synchronization | Own | Consume no live API | Hardware permits remain repository-local |
| Intrinsics, depth, fiducial, hand-eye, base/world, metric-scene calibration | Own evidence and estimates | Independently validate imported claims | Cross-repo receipt binds identities, units, transforms, uncertainty |
| Measured, appearance, inferred, and reference-only scene layers | Own | Consume | `WorkcellBundle` contract |
| Workcell frame/entity/relation graph and asset candidates | Own canonical representation | Translate into simulator inputs | Versioned schema and conformance fixtures |
| Web viewer and scan-quality product | Own | No ownership | Derived/public assets only; raw observations stay private |
| SO-ARM100 robot geometry and MuJoCo workcell compilation | Reference robot interface identity only | Own | Robot source remains SO-ARM100; no geometry copy into Robo Scan |
| Actuator, latency, gripper, contact, and task-conditioned twin calibration | Provide relevant observation evidence | Own simulator-side model and calibration | A future paired shadow runner executes through a separate safety boundary |
| Task, reward, evaluator, reset, curriculum, and cousin generation | No ownership | Own | Typed schemas may later move into a dependency-light contracts package |
| Episodes, LeRobotDataset, processor observation, policy training | No ownership | Own | Pinned LeRobot executes ML/data behavior |
| Strict grasp/task truth and policy qualification | No ownership | Own | Hardware-observable evaluator is a later shared contract |
| Whole-system authority, promotion, rollback, lineage | Local claims only | Own central composition | No producer artifact self-promotes |
| Policy hardware runtime | Scan-only hardware path | Governance and policy integration | Pinned LeRobot/leLab or a later conservative hardware-runtime package |

## Contract Stack

The projects should exchange a small hierarchy rather than one giant manifest.
Each layer is immutable and references the layer beneath it by schema and
content identity.

| Contract | Producer | Purpose | First eligible phase |
| --- | --- | --- | --- |
| `SceneExportReceipt` | Robo Scan | Self-contained manifest/assets, units, transforms, provenance, privacy, authority class, and candidate-only disposition | I1, reference-only fixture |
| `WorkcellBundle` | Robo Scan | Simulator-independent frame/entity/relation graph, measured/appearance/inferred layers, collision candidates, sensor specs, uncertainty, and source lineage | I4, after real M4 reconstruction |
| `CalibrationArtifactReceipt` (WCW-1 witness) | Robo Scan | As-built measured calibration witness: CAD/tag geometry identities, print/filament/slicer identities, measured dimensions and per-cartridge masses, fiducial acceptance results, and uncertainty; sim-link derives MuJoCo inertials from these measured values through its verified inertial intake | I4+, alongside the first metric capture |
| `TwinCandidate` | Sim-link | Workcell bundle reference plus SO-ARM100 identity, MuJoCo compiler identity, actuator/contact priors, and deterministic compiled artifacts | I3 reference-only shell; I5 metric candidate |
| `TwinRevision` | Sim-link | Candidate plus calibrated parameter posterior, supported action/observation interfaces, and validation results | I6 |
| `Task/Evaluator/Episode/Policy` artifacts | Sim-link | Foundry inputs, experience, model adaptation, and truth evaluation | Existing and later sim-link work |
| `FidelityCertificate` | Sim-link central composition | Task-family and operating-envelope qualification over exact upstream and downstream revisions | I6+ |
| `WorkcellDeploymentBundle` | Integration release | Exact twin, task/evaluator, policy, safety envelope, certificates, and lineage | I8 |

Do not create a shared Python package before the receipt semantics have been
implemented independently on both sides. Independent producer and consumer
validators are intentional defense in depth. Extract a dependency-light
`workcell-contracts` package only if two working schema versions show repeated
semantic drift. It may contain schemas, identifiers, coordinate conventions,
and pure validation helpers—never camera, robot, simulator, model, or file-I/O
implementations.

## Integration Phases

### I0 - Freeze The Boundary

**Owner:** both repositories.

**Actions:**

1. Keep the repositories and Git histories separate.
2. Ban sibling-checkout reads, path dependencies, submodules, and automatic
   discovery from production paths.
3. Preserve the accepted producer receipt identity and the independent sim-link
   compatibility lock; schema changes require a new producer-first boundary.
4. Keep sim-link's import guard against `environment_scanner` and `so101_scan`.

**Exit gate:** this roadmap and the permanent handoff contract are reviewed and
committed. No runtime capability is created.

### I1 - Producer Receipt Handshake

**Owner:** Robo Scan. **Status:** verified and remotely preserved by Brief 054
at `72eb02efe7e69981a5afab41a2733cd31ec03d4e`.

**Required output:** one checked-in, source-free reference-only export fixture
containing a canonical receipt, one sealed layered-scene manifest, and exactly
the declared relative assets.

**Required properties:**

- Exact receipt schema/version, export identity, and self-identity.
- Producer schema identity in the export; the producer package version and Git
  revision are published by the reviewed handoff and pinned in sim-link's
  compatibility lock rather than placed inside the self-checksummed receipt.
- Canonical file hashes, byte counts, media types, and relative paths.
- Units, axes, handedness, frame names, every finite rigid transform, and
  uncertainty/provenance summaries.
- `reference_only`, `metricAuthority: false`, and `twin_candidate_only` for the
  first fixture.
- No local paths, raw observations, symlinks, checkout references, hardware
  identifiers, mutable state, or global authority fields.
- Deterministic reopen plus tamper, path-escape, privacy, and authority-spoof
  tests.

**Exit gate:** the Robo Scan implementation, fixture, tests, state, review, and
remote commit agree. Sim-link receives the full commit ID, receipt identity,
schema identity, and fixture bytes—not a working-tree path.

### I2 - Independent Sim-Link Receipt Conformance

**Owner:** sim-link. **Status:** verified by Brief 145 at `67daad9`, hardened at
`cb4e5a0`, and adversarially covered at `d01416b`.

**Planned slice:**

- Add `scenesmith/robot_lab/robo_scan_export_receipt.py` as a pure offline
  validator. It must not import the producer package.
- Add `scripts/robot_lab/verify_robo_scan_export.py` for an explicitly selected
  export directory.
- Add `tests/unit/test_robo_scan_export_receipt.py` with the source-free I1
  fixture and adversarial mutations.
- Add `configurations/robot_lab/robo_scan_export_lock.json` binding the approved
  producer commit, receipt/schema identities, fixture identity, and allowed
  disposition.

**Validation:** strict JSON, finite numbers, canonical ordering, safe path
resolution, no symlinks, every byte/hash binding, proper rigid transforms,
known schema, privacy restrictions, exact authority class, and deterministic
reopen. Unknown, stale, contradictory, or metric-claiming reference evidence
is quarantined.

**Exit gate:** sim-link independently accepts the exact producer fixture and
rejects all declared mutations. This grants only
`robo_scan_reference_export_valid`; it does not create or change a simulation
scene.

### I3 - Reference-Only End-To-End Plumbing

**Owner:** sim-link. **Status:** reference-only descriptor boundary verified by
Brief 145; no metric geometry or simulator asset was created.

Add a narrow `robo_scan_workcell_adapter.py` that converts an accepted receipt
into an inspectable, non-metric `TwinCandidate` shell. The first adapter must:

- Retain every source node/asset identity, authority label, transform, and
  uncertainty field.
- Keep reference-only content outside collision, dynamics, calibration,
  training, and physical-qualification inputs.
- Emit a deterministic structural audit and optional non-colliding preview;
  it must not pretend relative units are metric MuJoCo geometry.
- Round-trip the fixture without opening hardware, loading a policy, or calling
  Robo Scan.

**Exit gate:** exact structural parity and deterministic identities pass. The
central composer continues to deny metric twin, training, transfer, and
promotion states.

### I4 - WorkcellBundle V1 In Robo Scan

**Owner:** Robo Scan; start only after its M1–M4 gates produce a real verified
metric reconstruction. Do not make this a substitute for those gates.

Extend the export semantics with:

- Canonical coordinate-frame graph in SI units.
- Stable entity IDs, semantic class, support/containment/visibility relations,
  and task-relevant regions without task or policy code.
- Separate visual, measured collision, inferred, and appearance assets.
- Collision-model candidates and their source/uncertainty, without asserting
  one as physically correct unless evidence selects it.
- Intrinsics/depth/sensor placement and measured calibration references.
- Geometry, pose, scale, sensor, and occlusion uncertainty with provenance.
- Robot interface identity, never a copied robot implementation.
- Held-out reconstruction/scale evidence and known limitations.

**Exit gate:** a real source-free metric bundle reopens independently, binds
the verified M4 evidence chain, and contains no raw/private source data.

### I5 - Metric Workcell To MuJoCo Twin Candidate

**Owner:** sim-link.

1. Admit the exact I4 bundle with the I2 validator and an updated compatibility
   lock.
2. Compile only measured/certified geometry into collision; preserve appearance
   and inferred layers as non-authoritative rendering/diagnostic inputs.
3. Compose the workcell with the pinned SO-ARM100 robot model and existing
   SO-101 action/observation interfaces.
4. Emit deterministic MuJoCo XML/assets plus a structural diff against the
   bundle: entity/frame counts, units, transforms, bounds, known dimensions,
   collision class, camera projection, and artifact identities.
5. Run static stability, reachability, collision, rendered-overlay, and
   independent scale tests.

**Exit gate:** `robo_scan_metric_workcell_candidate_valid` may become a local
capability claim. It still cannot grant `physical_twin_qualified`, training,
transfer, or promotion.

### I6 - Layered Twin Calibration And Fidelity

**Owners:** split by parameter class.

- Robo Scan owns geometry, scene frames, camera/depth, sensor placement, and
  reconstruction uncertainty.
- Sim-link owns actuator response, command timing, gripper mapping, contact
  dynamics, task sensitivity, domain randomization, and policy-facing
  interfaces.
- A later conservative hardware runtime executes bounded paired probes and
  emits proposed/issued/measured/timestamped traces; neither repository may
  bypass its safety gates.

Represent calibration as immutable priors, evidence, posteriors, and validity
envelopes. Never overwrite the source scene with one fitted point estimate.
Qualify geometry/sensor fidelity separately from task-conditioned dynamics and
policy robustness.

Calibration is two stages with different prerequisites. Instrument calibration
(camera intrinsics, hand-eye, robot/world frames, clock alignment, command
cadence/latency, joint tracking, gripper command-to-width mapping) is a
property of the capture and execution stack and may proceed with static poses
and scripted probes before any learned policy exists. Transfer calibration
(friction, contact discrepancy, task-event alignment) waits for a policy worth
transferring and a compiled metric twin, and fits only what the target task
family exercises.

The preferred first physical intake is the WCW-1 calibration witness. Robo
Scan owns its CAD, fiducial geometry, reference print profile, as-built
measurement protocol, and the `CalibrationArtifactReceipt`. Sim-link consumes
only the receipt through its verified measured-inertial intake, keeping
measured mass properties — never slicer density — as the source of compiled
MuJoCo inertials. The witness's gripper contact bands and push/lift probes
later provide transfer-calibration evidence through the paired trace runner.

**Exit gate:** held-out paired evidence, uncertainty, task-family envelope,
drift triggers, and central composition produce a scoped fidelity certificate.

### I7 - Deduplicate Active Paths

Begin deletion only after two independently verified metric handoffs and one
end-to-end sim-link compile. For every candidate, prove call-site migration,
feature parity, negative/adversarial coverage, and rollback before removal.

| Current surface | Final disposition | Retirement gate |
| --- | --- | --- |
| Robo Scan camera identity, RGB-D capture, scan planning/execution, reconstruction | Keep in Robo Scan | Canonical producer implementation |
| `live_readonly_observation.py` camera/census/capture path in sim-link | Freeze as historical, migrate new scene observation to Robo Scan exports, then remove active runtime entry points | Two metric handoffs; zero production call sites; historical artifacts/tests remain interpretable |
| `run_live_readonly_observation.py` and camera-manifest migration scripts | Retire from the active path after migration | Same gate plus explicit deprecation/replacement CLI proof |
| Sim-link `static_pose_*` evidence modules | Preserve until the imported metric path and central composer replace every active dependency; then separately score for retirement | No evidence rewrite; no caller; historical verification retained |
| Robo Scan layered-scene manifest/compiler | Keep as producer-side scene/export truth | Evolve through versioned schema, never replaced by sim-link |
| Sim-link `mujoco_export.py`, structural twin diff, twin contract | Keep as consumer/backend compiler and audit | Rebind to `WorkcellBundle`/`TwinCandidate` identities |
| Robo Scan geometry/sensor calibration | Keep in Robo Scan | Produces only local evidence/candidate claims |
| Sim-link action/gripper/dynamics calibration | Keep in sim-link | Rename/split fields if needed to prevent camera/geometry ambiguity |
| Sim-link `computed_twin_qualification.py` and `authority_composer.py` | Keep in sim-link | Consume imported local claims; remain the only system-level composer |
| Canonical JSON/hash/path validation on both sides | Keep independent | Intentional trust-boundary redundancy, not wasteful duplication |
| Raw scan sessions versus LeRobot episode data | Keep separate | Different privacy, lifecycle, and training semantics |
| Robo Scan viewer versus sim-link training/evaluation UI | Keep separate | Different product and dependency lifecycles |

**Exit gate:** the active production graph has one owner for every capability,
all removals have a reviewed dependency report, and no historical proof bytes
or authority interpretation changes.

### I8 - Whole Foundry Expansion

Only after the MVP exit gate, add the larger report's ideas incrementally. The
approved near-term sim-link cut is narrower and lives in the
[MVP execution plan](./sim-link-mvp-execution-plan.md). It pulls forward only
state-fork recovery data, a discrete uncertainty ensemble, observer roles, a
thin paired trace runner, and timing evidence. Posterior calibration, a broad
cousin algebra, fidelity/drift certificates, flight recording, skill graphs,
scientist tooling, alternate renderers/backends, world models, and residual
dynamics remain deferred or cut until evidence creates a need.

These remain sim-link/integration or hardware-runtime responsibilities. Robo
Scan should not absorb task, reward, episode, policy, or promotion systems.

## Compatibility And Release Protocol

Every cross-repository compatibility boundary follows this order:

1. Producer writes a brief, implements/tests the export, commits, reviews, and
   pushes.
2. Producer publishes the full commit, schema ID, receipt ID, fixture archive
   identity, and declared authority class.
3. Consumer copies only the source-free fixture bytes, never a local path.
4. Consumer pins those identities in its compatibility lock and implements an
   independent validator.
5. Both sides pass the same golden fixture plus their own adversarial tests.
6. Consumer records accepted/quarantined disposition without mutating producer
   state.
7. Schema changes start producer-first and require a new compatibility lock;
   the last verified version remains usable until migration passes.

Initial consumers accept exactly one schema version. Add an N/N-1 compatibility
window only after a real migration exists. Unknown fields fail closed unless
the schema explicitly declares an extension mechanism.

Do not use a Git submodule, subtree, editable install, sibling path, or broad
monorepo merge. If a pure shared package later becomes justified, pin its exact
release and keep it dependency-light.

## Rollback And Failure Rules

| Failure | Required response |
| --- | --- |
| Producer receipt or fixture changes without a version/identity change | Reject and quarantine; keep prior compatibility lock |
| Consumer validation disagrees with producer | Treat as contract defect; no scene change; resolve with a new producer or consumer slice |
| Reference-only content attempts metric/collision use | Reject and record authority spoofing failure |
| Metric bundle fails scale/transform/privacy/asset validation | Quarantine as a candidate; do not fall back to inferred authority |
| MuJoCo compile or structural audit regresses | Retain previous twin revision and disable the new adapter path |
| Imported twin fails paired fidelity | Recalibrate/narrow the envelope; do not train around an unidentified mismatch |
| Retirement breaks a caller or historical verifier | Restore the active path and treat deduplication as incomplete |
| Hardware discrepancy or drift exceeds certificate | Stop promotion, retain traces, and route to the owning calibration layer |

## Immediate Queue

1. **Sim-link now:** execute T20.17 clean `pi05_base` dataset-native training
   and strict-v2 evaluation under the current mechanical simulation authority.
2. **Sim-link next:** follow the local T20.18-T20.22 queue for state-fork
   recovery data, a discrete ensemble, observer-role evaluation, paired traces,
   and timing. Each task requires its own brief and dependency gate.
3. **Robo Scan separately:** resolve the gate/CLI mismatch so M1 gates invoke
   commands that exist, then pursue the first real M1 capture through an
   explicit time-boxed fallback ladder: known-good USB3 cable/port, powered
   hub, a Linux capture node emitting the same content-addressed bundles, and
   only then a declared degraded-authority fiducial-scaled monocular path.
   Complete M2-M4 before producing a metric I4 `WorkcellBundle`, and plan the
   WCW-1 witness print/measurement so the first
   `CalibrationArtifactReceipt` can accompany it. This roadmap grants none of
   those actions.
4. **Cross-repository wait:** sim-link opens I5 only after the exact verified I4
   bytes and an updated compatibility lock exist.
5. **Both later:** perform I7 deduplication only after two real metric handoffs
   and one end-to-end compile.

## Definition Of Integrated

The projects are integrated only when all of these are true:

- A source-free Robo Scan export can be selected without the producer checkout.
- Sim-link independently validates and pins every source/schema/byte identity.
- A real metric bundle compiles deterministically with SO-ARM100 into MuJoCo.
- Measured, appearance, inferred, reference-only, and simulator-derived facts
  remain distinct end to end.
- Geometry/sensor calibration and dynamics/policy calibration have named owners.
- Central authority can trace a decision through workcell, twin, dataset,
  processor, policy, evaluator, and evidence revisions.
- The active graph contains no duplicated capture/reconstruction implementation.
- Reference-only or failed imports cannot affect training, physical transfer,
  or promotion.
- The previous verified twin and policy can be restored without rebuilding
  history.

That is the merge: one inspectable workcell foundry, two focused repositories,
one explicit contract stack, and no ambiguous authority seam.
