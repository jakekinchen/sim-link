# Autonomous Milestones

This file defines invariant milestones for autonomous work on this project.

Milestones are required outcomes, not detailed subtasks. The Executor and Reviewer choose the implementation slices needed to satisfy the next milestone.

## Overall Goal

From a SceneSmith room description, produce a randomized SO-101 desk-sorting workcell, run policy episodes, allow a connected physical leader arm to take over the simulated robot under a deadman, resume autonomy, and save the resulting corrections as a verified LeRobot dataset. The same path must be demonstrable with a deterministic simulated leader when hardware is unavailable.

## Milestone Rules

- Milestones are invariant outcomes, not task lists.
- Agents choose implementation slices needed to satisfy the next milestone.
- The Reviewer may not mark a milestone complete without running or recording its verification gate.
- The Manager challenges work that optimizes beyond the current milestone before the gate is satisfied.
- If a milestone gate proves wrong or incomplete, update this file.

## M0 - Safety And Proof Contract

**Required outcome:** The architecture, no-follower invariant, proof-state vocabulary, intervention frame contract, and verification gates are encoded in tests and durable docs.

**Why this is invariant:** Human-in-the-loop robotics data is not trustworthy if policy proposals, human corrections, executed actions, and hardware boundaries can be conflated.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest tests.unit.test_robot_lab_intervention
rg -n "SO101Follower|send_action|follower_port" scenesmith/robot_lab/leader_arm_bridge.py scripts/robot_lab/run_randomized_intervention_eval.py
```

**Completion evidence:**

- Unit proof for deadman expiry, action arbitration, action clamping, and no-follower construction.
- A written contract distinguishing scripted failure injection from physical manipulation and neural-policy success.

## M1 - Valid Domain Randomization

**Required outcome:** Seeded randomization changes visual, geometric, sensor, and dynamics fields while keeping cubes, trays, the robot base, and the AprilTag in valid collision-free reachable placements.

**Why this is invariant:** Invalid resets measure scene-generation failures rather than policy robustness.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest tests.unit.test_robot_lab_intervention.DomainRandomizationTests
./.mujoco_venv/bin/python scripts/robot_lab/run_randomized_intervention_eval.py --output-dir outputs/robot_lab/so101_desk_cube_sort/intervention-proof --seed 4100 --episodes 3 --correction-source simulated_leader --force-failure
```

**Completion evidence:**

- Same-seed equality, different-seed variation, pairwise-clearance, and bounds tests.
- Per-episode manifests showing fields actually applied to exported MuJoCo XML.

## M2 - Control-Step Intervention

**Required outcome:** Every simulation control step selects exactly one executed action from the policy or leader source through an armed, fresh deadman; takeover and release are recorded without commanding a follower.

**Why this is invariant:** Post-hoc trajectory rewriting is not an intervention system and cannot produce valid DAgger-style supervision.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest tests.unit.test_robot_lab_intervention.InterventionArbiterTests tests.unit.test_robot_lab_intervention.LeaderBridgeTests
```

**Completion evidence:**

- Frame rows contain policy action, optional human action, executed action, source, deadman age, and intervention event.
- A read-only physical-leader smoke sample when its known port is free, with follower port unopened.

## M3 - Synchronized Episode Dataset

**Required outcome:** Randomized episodes save time-aligned side, overhead, and wrist observations with robot state and action labels; the exporter creates and reloads a LeRobot dataset without reusing final stills as fake temporal observations.

**Why this is invariant:** Fine-tuning quality depends on aligned observations and correction targets.

**Verification gate:**

```bash
external/leLab/.venv/bin/python scripts/robot_lab/export_intervention_dataset.py --episode-summary outputs/robot_lab/so101_desk_cube_sort/intervention-proof/randomized-episode-4100/intervention_episode_summary.json --output-root outputs/robot_lab/so101_desk_cube_sort/datasets/intervention-proof --overwrite --verify --allow-scripted-harness --frame-selection all
```

**Completion evidence:**

- Distinct frame paths and hashes across episode time.
- Reloaded dataset shapes, frame count, intervention count, and sidecar labels.

## M4 - Browser-Visible Takeover Loop

**Required outcome:** The existing SceneSmith action server can launch randomized batches, show live episode state and cameras, arm intervention, accept press-and-hold takeover, and report policy/human control transitions.

**Why this is invariant:** The operator needs one inspectable surface to recognize failure and correct it in time.

**Verification gate:**

```bash
node scripts/robot_lab/verify_robot_action_server.mjs --url http://127.0.0.1:8822/ --output-dir outputs/robot_lab/so101_desk_cube_sort/action-server-intervention-proof
```

**Completion evidence:**

- Browser screenshot and machine-readable verifier report.
- A plus-button episode and randomized intervention episode both complete without console errors.

## M5 - End-To-End Acceptance

**Required outcome:** Three randomized episodes include at least one detected failure and correction, all finish with truthful score summaries, their correction data exports and reloads, and the browser displays the resulting workcell and intervention state.

**Why this is invariant:** Unit pieces do not prove the operator workflow is usable end to end.

**Verification gate:**

```bash
scripts/audit_autonomous_workflow.sh
./.mujoco_venv/bin/python -m unittest tests.unit.test_robot_lab_scene_builder tests.unit.test_robot_lab_intervention
```

**Completion evidence:**

- Batch summary, trajectories, synchronized camera frames, dataset verification summary, browser report, and screenshots.
- Known limitations explicitly state whether the correction moved objects through real contact physics, a test-only scripted harness, or a human-operated physical-leader session.

**Completion audit:** `docs/so101-intervention-completion-audit.md` and
`outputs/robot_lab/so101_desk_cube_sort/completion-audit/intervention-system-completion.json`
both report pass on 2026-07-09.

## M6 - Git-Guarded Learning-Cycle Contract

**Required outcome:** Every learning cycle starts from a recorded clean Git
commit, uses a versioned configuration, writes a small append-only manifest, and
refuses ambiguous seed overlap, dirty learning-loop code, or unbounded external
compute commands.

**Why this is invariant:** A candidate model cannot be reproduced or audited if
the code, dataset recipe, training command, and evaluation gate are not tied to
one immutable source revision.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest tests.unit.test_pi05_autolearn
./.mujoco_venv/bin/python scripts/robot_lab/run_pi05_autolearn_cycle.py \
  --config configurations/robot_lab/pi05_autolearn.example.json --dry-run
```

**Completion evidence:**

- Config validation rejects overlapping train/evaluation seeds and unsafe
  physical-follower or unbounded Brev commands.
- Dry-run manifest records the current commit, stage commands, expected
  artifacts, and cleanup policy without starting training.

## M7 - Policy-Visited DAgger Corrections

**Required outcome:** Assisted neural episodes can export only explicitly logged
privileged controller or human correction frames as expert action targets, while
excluding scripted object motion and ordinary policy proposals.

**Why this is invariant:** DAgger depends on expert labels for states visited by
the learner; relabeling policy actions or fabricated cube motion would reinforce
the failure instead of correcting it.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest \
  tests.unit.test_robot_lab_intervention \
  tests.unit.test_pi05_autolearn
```

**Completion evidence:**

- Frame-selection tests cover direct policy frames, task-space recovery,
  task-space transfer, post-place control, human intervention, and scripted
  harness rejection.
- Export summaries report correction source counts and policy-versus-executed
  action deltas.

## M8 - Bounded Training And Cost Cleanup

**Required outcome:** A cycle launches one explicitly bounded fine-tune command,
captures its exit status and artifact hashes, and always executes/records the
configured Brev stop or delete cleanup before the cycle can finish.

**Why this is invariant:** Training must not silently run without limits or
leave paid compute alive after success or failure.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest tests.unit.test_pi05_autolearn
```

**Completion evidence:**

- Fake-runner tests prove cleanup runs after both training success and failure.
- The cycle manifest records training bounds, model artifact identity, and the
  final Brev inventory.

## M9 - Held-Out Promotion Or Rollback

**Required outcome:** Candidate and baseline are evaluated on the same complete
held-out seed set in pure-policy mode; promotion requires the configured success
rate, no controller assistance or physical-follower commands, and a non-regression
against the baseline. Rejected candidates remain recorded without replacing the
accepted pointer.

**Why this is invariant:** A single assisted 4/4 episode is a product milestone,
not evidence that a new checkpoint learned autonomous sorting.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest tests.unit.test_pi05_autolearn
```

**Completion evidence:**

- Promotion tests cover incomplete evaluation, assist contamination, success
  threshold, baseline regression, accept, and reject.
- The accepted checkpoint pointer changes only for a passing candidate and the
  decision manifest is committed separately from generated model data.

## M10 - Trusted PI0.5 Training Data Contract

**Required outcome:** Every base, correction, and runtime action uses one
versioned SO-101 coordinate and normalization contract; correction chunks are
temporally valid and retain the exact task prompt shown to the policy.

**Why this is invariant:** A bounded training run is not meaningful when its
expert targets use different joint coordinates, normalization, temporal order,
or language conditioning from the accepted data and runtime.

**Verification gate:**

```bash
./.mujoco_venv/bin/python -m unittest \
  tests.unit.test_robot_lab_intervention \
  tests.unit.test_pi05_autolearn
```

**Completion evidence:**

- One round-trip-tested transform is shared by expert, exporter, and runtime.
- Malformed bootstrap corrections are rejected by merge validation.
- Regenerated corrections have compatible statistics, task labels, and episode boundaries.

## M11 - Balanced Failure-Focused Replay

**Required outcome:** Training replay balances accepted/base behavior with
correction/context samples, covers pre-contact failures, and retains bounded
corrections across cycles.

**Why this is invariant:** Uniform sampling currently exposes a 25-step run to
only two correction frames and mostly teaches post-contact behavior even though
the strict policy fails before grasp.

**Verification gate:** source/phase sampling tests plus a rollout whose logged
exposure matches configuration and whose interventions include approach/grasp.

**Completion evidence:** sampler counts, context-window audit, trigger evidence,
and cumulative replay manifest.

## M12 - Honest Evaluation And Provenance

**Required outcome:** Evaluation reports stage progress and separates strict,
contact-stabilized, controller-assisted, and physical proof; runtime, seeds,
datasets, normalizers, processors, and checkpoints are content-addressed.

**Why this is invariant:** Terminal 0/4 alone hides regressions such as loss of
contact, and a contact-gated weld cannot be called strict autonomous success.

**Verification gate:** promotion/provenance tests and paired evaluation artifacts.

**Completion evidence:** stage metrics, disjoint seed registries, proof-mode
gates, pinned runtime manifest, and bounded evaluation storage.

## M13 - Meaningful Policy Improvement

**Required outcome:** Corrected candidates are trained at meaningful bounded
budgets, reloaded, compared on paired seeds, and either promoted or rejected with
an identified next change.

**Why this is invariant:** Five or 25 batch-one updates are pipeline smoke tests,
not evidence that PI0.5 can learn the sorting behavior.

**Verification gate:** corrected 250/500/1,000-step MPS ladder, action-horizon
ablation, and model-baseline comparison on the same proof contract.

**Completion evidence:** checkpoint hashes, sample exposure, paired metrics,
review decision, and accepted-pointer integrity.

**2026-07-10 rebaseline:** The 250-step rung is verified as historical
development evidence (reach 0.500 to 0.625, no grasp or task success). Rungs 500
and 1,000, the action-horizon sweep, and the model bakeoff are suspended until
M16-M18 verify the twin, compiled experience, and intentional mixture gates.

## M14 - Competence-Gated Domain Randomization

**Required outcome:** Visual, geometry, dynamics, latency, and calibration
variation expand through named levels only when the current policy clears the
previous level.

**Why this is invariant:** Uniformly broad randomization can hide basic learning
failure and produce conservative high-variance policies.

**Verification gate:** deterministic level manifests, held-out stress tiers, and
automatic advance/hold tests.

**Completion evidence:** per-level success curves and recorded curriculum decisions.

## M15 - Reward-Informed Improvement And Closeout

**Required outcome:** Simulator progress signals improve replay or policy
learning without reward hacking; bounded RL begins only after repeatable nonzero
strict success, followed by a final capability and sim-to-real readiness audit.

**Why this is invariant:** Sparse terminal RL cannot learn when all rollouts fail,
and simulation completion is not physical-robot proof.

**Verification gate:** reward ablation, bounded rollout budget, paired strict
evaluation, and final proof matrix.

**Completion evidence:** reward definitions, safety/budget logs, promotion or
rejection, Git history, and explicit remaining physical validation gates.

## M16 - Hardware Twin Foundation And Qualification Contract

**Required outcome:** SceneSmith uses a pinned, license-recorded SO-101 structural
baseline and can emit immutable TwinProfile and TwinQualificationReport artifacts
that distinguish sourced priors, measured overrides, fitted parameters,
uncertainty, and held-out predictive evidence.

**Why this is invariant:** A visually plausible MJCF is not proof that simulated
kinematics, gripper contact, actuator response, camera timing, or uncertainty
cover the real arm. Training must bind to an explicit twin identity and
qualification state.

**Verification gate:** Offline structural validation proves model source/hash,
named joints, inertials, ranges, gripper collision/contact setup, camera mount,
and no hardware access. Physical census/identification remains a separately
authorized gate and may not be fabricated.

**Completion evidence:** source pin and license, model comparison, TwinProfile
schema, offline profile artifact, qualification report, tests, and explicit
`simulation_only` versus `physical_qualified` state.

## M17 - Experience Compiler Truth Gate

**Required outcome:** Immutable raw rollouts compile deterministically into
contract-bound frame records, hard-boundary segments, and valid unpadded action
windows for horizons 5, 10, 15, and 50.

**Why this is invariant:** More training is misleading when labels, ownership,
prompts, coordinate semantics, or temporal windows are ambiguous.

**Verification gate:** Full-scan compiler validation reports zero accepted
invalid windows; collection, training, and inference fixtures produce identical
canonical/normalized tensors; a deterministic sampled-window audit succeeds.

**Completion evidence:** coordinate contract, normalization bundle,
`frames.parquet`, `segments.parquet`, `window_index.parquet`, schema/hash manifest,
and audit report.

## M18 - Intentional Experience Mixture And Branch Corrections

**Required outcome:** Training views are built from separate logical buffers with
source x task-phase x control-mode sampling, append-only cycles, exact simulator
progress, and snapshot-linked failure/correction branches.

**Why this is invariant:** Sampling composition and correction provenance must be
reproducible independently from reward weighting, and recovery must not be
misrepresented as a physical task phase.

**Verification gate:** One manifest reproduces exact sampled window IDs and
composition; branch-and-correct pairs share a correction event while preserving
immutable source rollouts; no source cell silently disappears.

**Completion evidence:** dataset-mixture manifest, exact draw audit, cumulative
registry, phase/progress predicates, branch linkage, and training-lock decision.

## M19 - Physical Hardware Twin Qualification

**Required outcome:** Explicitly authorized read-only census and bounded physical
experiments identify camera, kinematic, gripper, actuator, backlash, contact, and
timing distributions well enough that held-out real behavior falls inside the
simulated envelope.

**Why this is invariant:** CAD detail and simulated canaries cannot establish
predictive equivalence to this particular printed, wired, calibrated arm.

**Verification gate:** A preregistered TwinQualificationSpec passes on held-out
real trajectories and contacts. Bus reads, commanded motion, and contact testing
are separate authority boundaries.

**Completion evidence:** immutable census, calibration runs, fitted posterior,
held-out TwinQualificationReport, profile hash, and requalification triggers.

## M20 - Cheap Falsification And Clean Supervision

**Required outcome:** Clean compiled single-cube data can be overfit by a small
baseline and PI0.5; checkpoint, execution-horizon, and model-bakeoff experiments
then establish repeatable nonzero strict competence before broader improvement.
Terminal target occupancy is recorded separately from strict pick-and-place
success, which requires a complete ordered grasp, lift, bounded transport,
release, stable-placement, and retreat witness.

**Why this is invariant:** A larger training run should not diagnose a data path
that a tiny policy or tiny overfit cannot learn. A final-state-only success metric
can also reward a putt, slide, throw, teleport, or assisted completion and thereby
promote reward hacking as if it were autonomous manipulation.

**Verification gate:** One immutable split and proof contract support ACT and
PI0.5 overfit, the optimizer-update ladder, horizon sweep, and four-policy bakeoff.
Deterministic adversarial traces preserve truthful terminal outcomes while
rejecting strict success for missing or reordered stages, unsafe impact dynamics,
scripted motion, assistance contamination, and evaluator-state leakage into actor
inputs.

**Completion evidence:** exact sampled windows, optimizer-update accounting,
reloadable checkpoints, a source-bound semantic-success contract, paired phase
and outcome-versus-strict metrics, adversarial rejection evidence, and a
promotion/rejection decision.

## M21 - Improve A Competent Policy

**Required outcome:** Exact-progress reward-aware cloning and, only after stable
strict competence, a bounded deployment-honest residual policy improve held-out
behavior across a one-factor-at-a-time curriculum.

**Why this is invariant:** RL must improve a competent prior rather than hide
coordinate, temporal, normalization, ownership, or sparse-reward failures.

**Verification gate:** Uniform/balanced/RA-BC ablation precedes the residual-RL
readiness gate; every online run has residual, rollout, safety, and budget bounds.

**Completion evidence:** progress artifact, ablations, learner/client interface,
paired residual result, curriculum decisions, and accepted-pointer integrity.

## M22 - Physical Shadow And Closeout

**Required outcome:** Explicitly authorized shadow-mode tensor parity and a
separately authorized reduced-risk physical phase produce an honest final
capability and sim-to-real readiness audit.

**Why this is invariant:** Simulation success and physical qualification are
different proof states, and command review must precede actuation.

**Verification gate:** Read-only observation parity, no-actuation command review,
deadman/workspace safeguards, and bounded physical evidence are recorded separately.

**Completion evidence:** physical proof artifacts, final proof matrix, Git
history, and explicit unresolved safety/transfer gates.

## Rebased Execution Order

Execute `M16 -> M17 -> M18 -> M19 -> M20 -> M21 -> M22`. M16-M19 are
prerequisites, not claims that the earlier verified infrastructure was useless.
They replace the assumption that the existing aggregate and unqualified twin are
already adequate for more training. M20-M22 supersede the remaining M13-M15 work.
