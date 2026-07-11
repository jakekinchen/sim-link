# Overnight Authority, Twin, and Experience-Compiler Goal Loop

**Run window:** 2026-07-11, actual start `2026-07-11T02:14:07-05:00`;
extended by explicit owner steering to a ten-hour total window. Do not start a
new major slice after `2026-07-11T11:44:07-05:00`; hard closeout is
`2026-07-11T12:14:07-05:00` (CDT).

## Launch contract

Run this in a separate top-level Codex thread rooted at this repository. At the
start of that thread, create and continuously pursue one persistent Goal for the
mission below. Work as the sole agent in that thread. Do not spawn, delegate to,
request, or use subagents.

## Mission

Advance the SceneSmith SO-101 simulation-factory program on
`origin/codex/pi05-autolearn-loop` through the extended supervised window. Complete as many
verified, dependency-correct slices as the fixed window safely permits. Begin
with the central authority-composition foundation, then finish the production
measured-inertial compiler, then mechanically computed qualification, then the
offline no-write servo-census preflight. If those gates pass, perform the
owner-authorized live read-only census and synchronized observation, then
no-actuation preprocessing/policy-shadow/matched-replay proof. Prepare a finite
supervised micro-motion permit and plan. The latest owner message is the final
operator confirmation for that exact initial gate, so no second prompt is
required; execution still fails closed until every prerequisite and the signed
session permit validate. If time remains
after those gates, begin one coherent M17 Experience Compiler foundation slice.
Do not stop after the first accepted slice: update state, commit, push, confirm
the remote, and continue until closeout or a genuine authority boundary.

The quality target is mechanically enforceable evidence semantics, not a large
number of superficially completed tasks. Completing T16.2b-A and T16.4b deeply
is more valuable than racing through later tasks.

## Source of truth

Use these sources in descending authority:

1. `AGENTS.md` and any applicable nested `AGENTS.md`.
2. The latest explicit owner instruction, including the 2026-07-11 supervised
   physical-proof steering recorded in this prompt, and the latest reviewer
   decision.
3. `GOAL.md`.
4. `docs/autonomous-workflow/project_state.json` for dynamic state.
5. `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`.
6. The active numbered brief, beginning with
   `docs/briefs/034-central-authority-composition-foundation.md`.
7. The latest relevant implementation commits, tests, generated artifacts,
   session log, and reviewer decision.
8. Older workflow records only when a current contract, test, or decision
   depends on them.

Do not recursively read every historical brief, log, or reviewer message.
Confirm the branch, HEAD, upstream, and dirty paths before editing. Preserve all
unrelated dirty files and saved dirty-worktree evidence.

## Expected starting state

Verify rather than assume:

- Branch: `codex/pi05-autolearn-loop`.
- Remote: `origin/codex/pi05-autolearn-loop`.
- Reviewed base before overnight substrate: `3cd142e`.
- T16.1b: verified at `dca2b45`.
- Unified executable LeRobot stack identity:
  `c8e903e7f1b75215864719398c902d864d8cbd7f43e01f03ffb22c8de240a7a4`.
- T16.4b strict artifact/authority sub-slice: implemented at `69df54d` and
  recorded at `3cd142e`; T16.4b is still incomplete.
- T16.2b-A: verified at `c0b9629`, with remote closeout through `0d67b8f`.
- T16.4b: active; T16.2b, T16.5a, T16.5b, T16.5c, and T16.6 follow.
- `training_lock`: closed.
- Conditional supervised hardware authority now exists only as specified below.
  No optimizer, physical-transfer, deployment, promotion, or unattended-motion
  authority exists.
- The checkout contains unrelated pre-existing dirty SceneSmith paths. They are
  not part of this goal.

If observed state differs, correct the canonical state to the evidence before
continuing. Never erase or fold unrelated changes into a robotics commit.

## Decision status

### Confirmed requirements

- The inertial artifact exposes local capabilities and evidence only.
- One central composer is the only production path that grants global system
  authority.
- Qualification results are computed and independently recomputed, never
  manually declared.
- T16.5a remains offline and no-write; no live device is opened before it is
  verified.
- T16.5b may perform live read-only identity/census/camera observation only
  after T16.5a is verified and while the owner is physically present.
- No write, torque change, or motion occurs until the finite, signed,
  content-addressed, session-scoped T16.6 permit and exact initial motion plan
  mechanically validate under an active owner-presence lease.
- M17 produces immutable, deterministic training-view artifacts without
  optimizer work.
- Every accepted slice is reviewed, committed, pushed, and confirmed on the
  named remote branch before the next slice begins.

### Recommended defaults

- Prefer explicit typed contracts and stable IDs over implicit booleans.
- Version schemas when safe compatibility would otherwise make authority
  ambiguous.
- Keep current-arm physical artifacts blocked until real measurements exist.
- Use fixture evidence only to prove production code paths, never physical
  qualification.

### Owner-only decisions

- The owner has conditionally granted live read-only hardware discovery,
  census, and camera capture after verified T16.5a, while physically present.
- The owner has granted final operator confirmation for one exact initial
  supervised micro-motion permit. No second prompt is required. The grant is
  valid only after all prerequisite gates and permit checks pass, while the
  owner-presence lease is active, and only for current-pose/no-op-equivalent
  first followed by at most one small one-joint displacement and exact return.
- Any material expansion beyond that exact initial permit.
- Any hardware access beyond the bounded T16.5b/T16.5c/T16.6 sequence.
- Optimizer training while the lock is closed.
- Paid or external compute.
- Destructive data changes, secrets, repository administration, merges,
  force-pushes, or material scope expansion.

## Authority model

Component artifacts report scoped facts such as:

```json
{
  "capabilities": {
    "artifact_schema_valid": true,
    "inertial_compilation_valid": true,
    "inertial_model_usable_for_simulation": true,
    "physical_measurement_evidence_verified": false
  }
}
```

They do not set global outcomes. The central composer derives:

```text
simulation_training_ready
  = structural_contract_valid
  AND executable_stack_valid
  AND coordinate_contract_valid
  AND normalization_contract_valid
  AND experience_compiler_valid
  AND required_simulation_properties_available

physical_transfer_ready
  = simulation_training_ready
  AND physical_hardware_identity_verified
  AND actuator_and_timing_qualification_passed
  AND camera_qualification_passed
  AND contact_qualification_passed
  AND held_out_twin_metrics_passed

promotion_eligible
  = policy_artifact_and_training_provenance_valid
  AND appropriate_evaluation_tier_passed
  AND required_deployment_authority_present
  AND no_safety_or_proof_state_violation
```

Every global decision must include explicit satisfied prerequisites, missing
prerequisite IDs, denial reason codes, consumed evidence identities, and a
deterministic composition identity. Missing, stale, contradictory,
synthetic-only, fixture-only, replay-only, unauthorized, or subject-mismatched
evidence fails closed.

## Authorization

You may:

- Read and edit in-scope repository files.
- Add focused production code, schemas, tests, fixtures, briefs, logs, reviewer
  decisions, and canonical workflow-state updates.
- Run non-destructive local tests, linters, compilers, fixture generators, and
  verification commands.
- Make routine in-scope design decisions.
- Create scoped commits and push verified commits only to
  `origin/codex/pi05-autolearn-loop`.
- Correct stale project documentation when repository evidence proves it.
- After T16.5a is verified, and only while the owner remains present, perform
  bounded hardware discovery, a live read-only census, synchronized camera
  observation, real-observation preprocessing, policy shadow, and matched
  MuJoCo replay with no actuation or writes.
- Prepare the exact finite T16.6 supervised-motion plan and generate the required
  session permit. The latest owner message supplies final confirmation for the
  exact initial permit, so execute only after the permit and every prerequisite
  mechanically validate; do not request a second confirmation.

You may not:

- Spawn or use subagents.
- Open any live serial, camera, leader, follower, servo-bus, or physical-robot
  surface before T16.5a is verified, or outside the staged authority above.
- Write a motor register, change torque state, or cause motion before the
  verified T16.6 session permit, plan, owner-presence lease, watchdog, stop, and
  shutdown gates all pass.
- Use open-ended policy actuation, deploy a newly trained checkpoint, run
  residual RL, or allow unattended motion.
- Run optimizer training while `training_lock` is closed.
- Start paid or external compute, including Brev.
- Merge, rebase shared history, force-push, open or merge a pull request, delete
  branches, or change repository permissions.
- Delete or overwrite user data, unrelated dirty paths, saved evidence,
  checkpoints, or datasets.
- Relabel fixture, synthetic, simulation, documentation, or replay evidence as
  physical evidence.
- Grant global authority from a component artifact.
- Claim a test, qualification, commit, push, or runtime behavior that was not
  actually verified.

When one task is blocked, record the blocker and continue another safe,
dependency-compatible task when possible. Escalate only when progress truly
requires owner-only authority.

## Priority 1 - T16.2b-A authority composition foundation

Implement Brief 034 before extending incompatible inertial output.

Acceptance criteria:

- Define versioned, machine-readable capability claims, prerequisite
  expressions, global decisions, denial reasons, and stable prerequisite IDs.
- Bind positive capability claims to content-addressed evidence, subject,
  scope, provenance class, freshness/validity, and authority identity.
- Reject unknown, duplicate, cyclic, ambiguous, stale, contradictory,
  synthetic-only, fixture-only, unauthorized, and subject-mismatched inputs.
- Make the composer the only production code path capable of granting
  `simulation_training_ready`, `physical_transfer_ready`, or
  `promotion_eligible`.
- Reject or explicitly deny forged global-authority fields carried by component
  artifacts.
- Emit deterministic decisions with satisfied and missing prerequisites,
  denial reason codes, evidence identities, and composition identity.
- Add adversarial tests proving overclaiming component payloads cannot produce
  global readiness.
- Amend Brief 033 and affected schemas before the production inertial compiler
  writes its new output.
- Preserve compatibility only where semantics stay unambiguous; otherwise bump
  the schema and deterministically regenerate fixtures.

Completion grants only `authority_composition_contract_valid`. It grants no
training, physical, transfer, deployment, or promotion authority.

## Priority 2 - T16.4b production measured-inertial compiler

Finish the production path in the amended Brief 033.

Structural and source requirements:

- Use a hierarchical acyclic BOM.
- Every non-root component has exactly one parent.
- Required leaf coverage forms an exact cover.
- Parent and descendant measurements cannot be selected together.
- Every selected component has one unambiguous transform path to its target
  rigid-body frame.
- Support `cad_scaled`, `direct_inertia_tensor`, `primitive_geometry`,
  `point_mass`, `lumped_component`, and `measured_rigid_assembly`.
- A scale reading proves mass only. Every source mode explicitly states how COM
  and inertia are derived or measured.
- Require explicit native and canonical units for mass, length, and inertia.
- Require device and calibration identity for measured inputs.
- Preserve raw values, SI conversions, repeatability, resolution, uncertainty,
  inherited assumptions, and CAD/approximation uncertainty.
- Preserve full internal precision through transforms and parallel-axis
  aggregation; round only final serialized output.
- Produce a deterministic production-schema fixture through the real production
  code path, explicitly labeled fixture evidence rather than current-arm
  physical evidence.
- Produce golden aggregate mass, COM, and inertia.
- Keep the checked-in current-arm artifact blocked until real measurements
  exist.
- Output inertial local capabilities only; never global readiness.

Numerical hardening:

- Add convergence and residual validation to the deterministic eigensolver.
- Use scale-relative tolerances.
- Compare randomized tensors against `numpy.linalg.eigvalsh`.
- Test rotation invariance, tiny and large scales, near-singular PSD tensors,
  and slightly indefinite tensors.
- Reject non-finite intermediate and output values.

## Priority 3 - T16.2b mechanically computed qualification

- A caller cannot manually declare a metric pass.
- The report generator computes each result from the pinned specification.
- The verifier independently recomputes each decision.
- Require exact unit agreement or an explicit validated conversion.
- Require finite values, sample count, held-out trajectory IDs,
  content-addressed evidence identity, valid environmental conditions, and
  uncertainty/confidence information.
- Route every global authority decision through the central composer.
- Prevent a profile from pre-authorizing the report that qualifies it.
- Add adversarial tests for status/tolerance disagreement, missing evidence,
  wrong units, stale profile references, evidence substitution, and fixture
  evidence impersonating physical evidence.

## Priority 4 - T16.5 staged census and observation proof

Begin only after T16.2b and T16.4b satisfy their declared gates.

### T16.5a - Offline no-write transport and lifecycle preflight

- Define a narrow read-only bus protocol; never pass the writable Feetech bus
  interface into census code.
- Audit construct, connect, read, decode, close, exception cleanup, and retry.
- Reject all write-like operations.
- Ensure disconnect and cleanup cannot disable torque or write registers.
- Report explicit operation counts, including zero register writes and
  `physical_follower_commanded=false`.
- Bind hardware role to stable identity where available: USB VID/PID, serial
  number, bus protocol, baud, servo models, and expected servo IDs.
- Reject follower identities and aliases, not only one hard-coded port path.
- Add recorded read-only trace fixtures and malformed, write-attempt,
  wrong-device, wrong-shape, missing-register, retry, and teardown-write tests.
- Name the offline result `census_trace_conformant` or equivalent. Do not call it
  physically qualified.
- Never open live hardware during T16.5a.

### T16.5b - Live read-only census and synchronized observation

Begin only after verified, committed, pushed, and remotely confirmed T16.5a,
with the owner physically present.

- Resolve and bind stable USB identity, bus protocol, baud, six expected servo
  IDs and models, and reject aliases or follower/device mismatch.
- Read identity/telemetry registers only. Record exact operation counts and
  prove zero configuration, torque, or register writes and no motion.
- Capture synchronized camera frames and timestamps without changing device or
  robot configuration.
- Emit a content-addressed immutable trace with
  `physical_follower_commanded=false` and the proof label
  `live_read_only_census_observed`.
- Any unexpected write, identity/calibration mismatch, telemetry loss, or
  operator absence closes all live resources and returns to offline-only work.
- This task grants observation evidence only, never physical qualification.

### T16.5c - No-actuation observation, shadow, and replay

Begin only after verified T16.5b.

- Compile real observations through the production preprocessing path, retaining
  raw frames, timestamps, requested transforms, and output identities.
- Run PI0.5 policy shadow only: compute proposed actions without sending them.
- Run matched MuJoCo replay against the same observation/task context, with no
  physical actuation.
- Use only `physical_observation_capture` and `policy_shadow` proof labels.
  Matched replay remains simulation/replay evidence.

## Priority 5 - T16.6 supervised physical proof of concept

Begin only after T16.5a-T16.5c are verified and the owner-presence lease remains
active. The latest owner message is final confirmation for the exact initial
micro-motion gate; no second prompt is required. It is not authority for any
expanded motion.

Before the first operation that can write a motor register, change torque, or
cause motion, generate, validate, sign, content-address, and persist a
session-scoped `physical_session_permit` bound to the exact resolved device,
six servo identities/models, calibration identity, current pose, units,
limits, telemetry, operator-presence lease, and a finite plan containing:

- every proposed write;
- starting pose;
- one-joint displacement and exact return;
- joint, speed, workspace, and collision limits;
- current, temperature, and voltage thresholds;
- maximum command count;
- deadman and stop method;
- maximum duration;
- shutdown sequence; and
- resulting proof label.

Mechanically prove that this is the smallest conservative
`supervised_micro_motion` plan: current-pose/no-op-equivalent first, then at
most one small displacement on one joint and exact return. The initial permit
must forbid every other joint, gripper motion, reach, contact, task primitive,
and policy-proposed actuation. Record proposed writes, maximum per-joint delta,
joint/workspace bounds, current/temperature/voltage thresholds, telemetry
timeout, command-count limit, lease, deadman/stop mechanism, duration, shutdown,
and proof label. Record requested, projected, sent, and measured values
separately.

If any identity, calibration, limit, unit, watchdog, stop method, shutdown
proof, permit signature/hash, or lease is missing or contradictory, do not move
and do not seek broader permission; record the blocker and continue offline.

Any identity/calibration mismatch, unexpected write, direction disagreement,
telemetry loss, threshold breach, workspace violation, unexpected contact, or
operator absence triggers immediate safe shutdown and offline-only work. Use
only `supervised_micro_motion`, `scripted_or_teleoperated_physical_task`, or
`policy_projected_assisted` as applicable. Never call these strict autonomous
physical success or physical qualification.

## Priority 6 - One safe M17 Experience Compiler foundation slice

Begin only if Priorities 1-5 are verified or safely stopped at their explicit
authority boundary, remotely preserved, and enough time
remains for a coherent slice. Do not train.

The truthful compilation path is:

```text
immutable raw rollout
  -> frame records
  -> hard-boundary segments
  -> valid action-window index
  -> normalization and preprocessing bundle
  -> deterministic replay audit
  -> training view
```

Target outputs:

- `frames.parquet`
- `segments.parquet`
- `window_index.parquet`
- `normalization_bundle.json`
- `compiler_manifest.json`
- `quarantine_manifest.json`

Choose one coherent first slice from immutable raw rollout/frame schemas, pure
coordinate transformation separated from validation and safety limiting,
normalization bundle plus real-processor parity, hard-boundary segments, or
valid action-window identity. Replace ambiguous transform behavior with three
explicit operations: pure coordinate transform; range/contract validation; and
safety limiting with requested-versus-executed logging.

## Longer dependency roadmap

Do not skip to these phases tonight, but preserve their requirements in every
contract:

- M18: episode-first source/phase/control-mode sampling; append-only correction
  cycles; exact simulator-state phase/progress; snapshot branches from
  pre-contact failures; immutable failure/corrected branches linked by
  `correction_event_id`; deterministic mixtures with stable window IDs.
- Simulation Gate C, only after simulation-training authority: tiny ACT and
  PI0.5 overfits; MPS 250/500/1,000 optimizer-update ladder; PI0.5 horizons
  5/10/15; phase-level one-cube evaluation; PI0.5 versus SmolVLA, ACT, and
  Diffusion Policy. Its strongest outcome is `simulation_policy_accepted`, not
  `physical_transfer_ready`.
- Physical qualification as a separate owner-authorized track: read-only
  identity census; camera/offset/kinematic/timing calibration; actuator,
  saturation, delay, friction, backlash, compliance, gripper, slip, and contact
  identification; held-out twin metrics; posterior distribution and
  requalification triggers.
- Policy improvement only after repeatable nonzero autonomous competence:
  exact-state progress-weighted cloning, SARM-compatible learned progress,
  bounded residual/action-expert RL, one-factor curriculum, strict audit-seed
  promotion, and owner-authorized physical shadow evaluation.

## Slice execution loop

For every slice:

1. Inspect the relevant production path, tests, active contracts, and current
   scoped Git diff.
2. Write or amend the smallest precise brief and acceptance criteria.
3. Mark the task `in_progress` in `project_state.json` before significant code.
4. Add deterministic tests first where practical.
5. Implement the smallest coherent production solution.
6. Run focused tests.
7. Run the relevant broad regression gate.
8. Perform a fresh same-agent review of the complete scoped diff. Search for
   authority escalation, stale references, unsafe defaults, non-finite values,
   graph ambiguity, double counting, evidence spoofing, path aliasing, cleanup
   side effects, nondeterminism, and documentation contradiction. Add an
   adversarial test for each material issue found.
9. Re-run verification.
10. Update only `project_state.json`, the active ledger, the required session
    log, and the reviewer decision. Avoid narrative duplication.
11. Create a scoped commit using explicit paths.
12. Push only to `origin/codex/pi05-autolearn-loop`.
13. Confirm the remote branch contains the commit.
14. Check remaining wall-clock time and continue to the next eligible task.

Do not call a slice verified until implementation, tests, review, documentation,
commit, and remote preservation agree.

## Canonical project-state contract

Maintain, with truthful semantics:

- branch and observed HEAD;
- last reviewed implementation commit;
- current task and dependency state;
- `training_lock`;
- source commit, brief ID, and review decision ID;
- exact test commands and outcomes;
- production artifact and contract identities;
- authority granted and explicitly not granted;
- known limitations and blocker evidence;
- precise next eligible task.

Resolve contradictions between canonical JSON and prose. A task cannot be
verified with a pending commit, missing review decision, unrun test, missing
remote proof, or authority exceeding its evidence. Mark superseded scaffolds
with `superseded_by` when a later production task owns their remaining work.

## Quality and evidence rules

- Prefer correctness, explicit semantics, and evidence over code volume.
- Keep public APIs typed and narrow.
- Avoid abstractions outside the active acceptance criteria.
- Use strict canonical serialization and content-addressed references at
  artifact boundaries.
- Never silently clamp, normalize, infer units, choose a prior, resolve BOM
  ambiguity, or convert evidence class.
- Preserve requested and executed values wherever limiting occurs.
- Every authority grant is mechanically derived and independently verifiable.
- Do not catch broad exceptions to turn failures into apparent success.
- Use primary source code and official documentation when external research is
  necessary; record exact revisions.
- After sufficient context exists, search the symbols and contracts being
  changed instead of exploring the repository broadly.
- Evidence must name exact changed files, test commands/results, artifact
  identities, proof class, known limitations, commit, remote confirmation, and
  unresolved adversarial cases.

## Progress updates

Start with a concise statement of the observed state and first slice. Then
report only meaningful verification and commit boundaries:

```text
Current task:
State:
Completed:
Evidence:
Commit and remote proof:
Authority gained:
Authority withheld:
Remaining:
Blockers:
Time remaining:
Next step:
```

## Time budget

- Record the actual executor start in its session log.
- Actual start: `2026-07-11T02:14:07-05:00`.
- Hard deadline: `2026-07-11T12:14:07-05:00`.
- At `2026-07-11T11:44:07-05:00`, do not start another major slice.
- Finish the current coherent edit, run the strongest affordable verification,
  revert or isolate speculative incomplete work, update state truthfully,
  commit and push any verified partial slice, and leave no ambiguous in-scope
  worktree changes.
- The deadline never permits weaker validation or inflated claims.

## Stop conditions

Stop the overnight run only when:

- The hard closeout point is reached.
- Every eligible safe milestone in this prompt is complete.
- Continuing requires hardware outside the conditional authorization, secrets,
  external spend, destructive action, repository administration, merge
  authority, an inactive owner-presence lease, or a missing/invalid exact
  physical-session permit.
- The repository or tool environment is corrupted after three materially
  different safe repair attempts.

A failing test, difficult implementation, uncertainty, or one blocked subtask
is not sufficient. Diagnose, make the safest in-scope decision, record the
evidence, and continue another dependency-compatible path when possible.

## Final handoff

End with:

- Final branch and HEAD.
- Every commit created and confirmed on the remote.
- Tasks completed, reopened, blocked, or left in progress.
- Exact focused and broad tests with outcomes.
- Artifact, schema, capability, and authority-contract identities changed.
- Authority gained and authority still withheld.
- Remaining risks and failed adversarial cases.
- The precise next task and acceptance criteria.
- Git status for in-scope and unrelated paths.
- Confirmation that no subagents, optimizer training, paid compute, merge,
  rebase, force-push, pull request, or destructive action was used; if bounded
  hardware work occurred, list every live operation, write/motion confirmation,
  shutdown result, and exact proof label instead of implying broader proof.
- Brev inventory and cleanup result if and only if later owner authority caused
  Brev to be used; otherwise explicitly say Brev was not started.
