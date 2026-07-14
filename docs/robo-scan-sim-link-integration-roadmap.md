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

At the time this roadmap was written, the separate Robo Scan thread had an
uncommitted active Brief 054 for an immutable, source-free scene-export
receipt. That is the correct producer-side starting slice. Its worktree must
remain owned by that thread; sim-link must wait for a committed producer
boundary before implementing a consumer.

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
3. Preserve Robo Scan's active dirty Brief 054 worktree; do not steer it into
   sim-link code.
4. Keep sim-link's import guard against `environment_scanner` and `so101_scan`.

**Exit gate:** this roadmap and the permanent handoff contract are reviewed and
committed. No runtime capability is created.

### I1 - Producer Receipt Handshake

**Owner:** Robo Scan; its active Brief 054 already defines this slice.

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

**Owner:** sim-link; start only after I1 is remotely preserved.

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

**Owner:** sim-link.

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

Only after I6 is credible, add the larger report's ideas incrementally:

1. Probabilistic `TwinRevision` and calibrated uncertainty cousins.
2. Task/evaluator contracts with hardware-observable parity.
3. Paired shadow runner and event-triggered flight recorder.
4. Task-conditioned fidelity and drift certificates.
5. Skill graphs, counterfactual checkpoints, recovery data, and broader cousins.
6. Multimodal scientist tools that propose bounded experiments but never enter
   the real-time safety loop.
7. Final `WorkcellDeploymentBundle` with complete lineage and rollback.

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

1. **Robo Scan thread:** finish Brief 054 exactly as scoped, commit/review/push
   the immutable reference-only export receipt, then return to the first open
   M1 gate. Do not add sim-link code or expand into policy/twin qualification.
2. **Sim-link:** wait for the verified Brief 054 commit. Then open I2 as one
   offline receipt-validator slice with no simulator or hardware behavior.
3. **Sim-link follow-up:** run I3 reference-only structural plumbing and prove
   that all global authority remains denied.
4. **Robo Scan:** finish M1–M4 before producing a real metric
   `WorkcellBundle`.
5. **Sim-link:** execute I5–I6 only from that verified metric export.
6. **Both:** perform I7 deduplication after two real handoffs, never before.

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
