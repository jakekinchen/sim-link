# Requirements And Contract Index

This index explains what must be true for the active program. It routes to the
canonical code, configuration, and workflow source; it does not duplicate live
authority decisions from `project_state.json`.

## Requirement Families

| Requirement | Rule | Canonical sources |
| --- | --- | --- |
| R1: Evidence integrity | Every referenced artifact is canonical-JSON signed, content-addressed, finite, and fail-closed on drift. | [`artifact_contract.py`](../scenesmith/robot_lab/artifact_contract.py) and the relevant signed configuration |
| R2: Stack identity | The executed LeRobot checkout, patch set, environment, and runtime must match the approved identity. | [`lerobot_stack.py`](../scenesmith/robot_lab/lerobot_stack.py), [`verify_lerobot_stack.py`](../scripts/robot_lab/verify_lerobot_stack.py) |
| R3: SO-101 semantics | Requested, projected, sent, and measured values remain distinct; coordinate conversion round-trips within its declared contract. | [`so101_processor.py`](../scenesmith/robot_lab/so101_processor.py), [`so101_canonical_processor_contract.json`](../configurations/robot_lab/so101_canonical_processor_contract.json) |
| R4: Grasp truthfulness | A successful grasp needs the strict antipodal witness, phase gates, no prohibited assistance, and release semantics—not merely object placement. | [`strict_grasp.py`](../scenesmith/robot_lab/strict_grasp.py), [`gripper_contact_semantics.py`](../scenesmith/robot_lab/gripper_contact_semantics.py) |
| R5: Constructive source behavior | The verified grasp is geometry-derived; retired broad candidate searches cannot return through a wrapper. | [`geometry_derived_grasp_primitives.py`](../scenesmith/robot_lab/geometry_derived_grasp_primitives.py), [recreation map](./autonomous-workflow/bespoke-package-recreation-map.md) |
| R6: Dataset provenance | Episode source, eligibility, quarantine, metadata, and frame content bind to one actual `LeRobotDataset`; no second training store is created. | [`lerobot_native_episode_manifest.py`](../scenesmith/robot_lab/lerobot_native_episode_manifest.py) |
| R7: Processor fidelity | Normalization, renaming, tokenization, and image preparation are observed by executing the pinned package pipeline, not re-derived by SceneSmith. | [`lerobot_actual_processor_observation.py`](../scenesmith/robot_lab/lerobot_actual_processor_observation.py) |
| R8: Training authority | Training stays closed unless the central composer mechanically grants `simulation_training_ready`. | [`authority_composer.py`](../scenesmith/robot_lab/authority_composer.py), [`pi05_authority_composition_contract.json`](../configurations/robot_lab/pi05_authority_composition_contract.json), [state](./autonomous-workflow/project_state.json) |
| R9: Physical boundaries | A read-only observation, a policy result, and physical proof are distinct; no hardware is accessed without separate live authority. | [`hardware_execution_profile.py`](../scenesmith/robot_lab/hardware_execution_profile.py), [live-adapter contract](./autonomous-workflow/minimal-live-adapter-recreation.md) |
| R10: Cost control | External or Brev compute must be explicitly bounded and cleaned up; it is not inferred from a training request. | [`autolearn_cycle.py`](../scenesmith/robot_lab/autolearn_cycle.py), [milestone M8](./autonomous-workflow/09-autonomous-milestones.md) |
| R11: Scan/calibration handoff | A Robo Scan export is explicit, immutable, checksum-bound, coordinate-complete, provenance-labelled, and locally scoped; no source checkout or artifact can grant whole-system authority. | [Robo Scan integration boundary](./robo-scan-integration.md), [`artifact_contract.py`](../scenesmith/robot_lab/artifact_contract.py), [`authority_composer.py`](../scenesmith/robot_lab/authority_composer.py) |
| R12: Observer and timing truth | Privileged simulator facts and hardware-observable facts use explicit roles; every timed stream names its clock; proposed, issued, and measured/applied actions remain separate. | [MVP execution plan](./sim-link-mvp-execution-plan.md), future T20.20-T20.22 contracts |

## Claim Vocabulary

Use these labels precisely.

| Label | Means | Does not mean |
| --- | --- | --- |
| Fixture / synthetic | Deterministic test or generated input | source experience or physical observation |
| Simulation / replay | MuJoCo or deterministic source replay result | trained-policy success or physical transfer |
| Processor observation | Actual pinned package preprocessing output was observed | policy model was loaded or inference ran |
| Simulation training ready | Central authority accepted the declared simulation training inputs | policy is competent, physical, or promotable |
| Policy evaluation | A bounded policy-owned simulation evaluation ran | strict task success unless the evaluator says so |
| Physical read-only | Owner-permitted live observation evidence | hardware motion, calibration, or qualification |
| Physical proof | Separately authorized physical task evidence | automatic promotion |
| Robo Scan reference-only export | Upstream visual or synthetic context admitted as a labelled simulation adjunct | measured geometry, metric calibration, or physical-twin qualification |
| Robo Scan metric candidate | Upstream measured artifact whose receipt and local facts can be validated | a system-level grant before central authority composition |

## Authority Rules

1. Component artifacts may expose local capabilities only.
2. The central authority composer makes system-level decisions.
3. Missing, stale, contradictory, synthetic-only, fixture-only, or unauthorized
   evidence fails closed.
4. Runtime access configuration and owner authority are independent. A
   no-prompt shell profile is neither a live permit nor a motion permit.
5. A training result, policy result, or physical observation never changes the
   authority state by implication; it needs its declared composition contract.

## Review And Verification

For any material change, follow the workflow:

1. Write a numbered brief with objective, contract, acceptance criteria, and
   explicit out-of-scope boundary.
2. Implement a narrow slice and run focused plus relevant broad regression
   gates.
3. Conduct the same-agent adversarial review: authority escalation, stale
   references, evidence spoofing, non-finite values, graph ambiguity,
   nondeterminism, and documentation drift.
4. Update state, active ledger, session log, and reviewer decision; commit and
   confirm the scoped remote boundary.

The executable workflow is in [Autonomous workflow](./autonomous-workflow/README.md).
The current authority values are only in
[`project_state.json`](./autonomous-workflow/project_state.json).

## Contract Navigation

| Need | Start at |
| --- | --- |
| Current task and current authority | [`GOAL.md`](../GOAL.md) + [`project_state.json`](./autonomous-workflow/project_state.json) |
| Exact configuration / signed payload | `configurations/robot_lab/` plus the implementation’s verifier |
| Dataset and provenance | [`experience_records.py`](../scenesmith/robot_lab/experience_records.py), [`lerobot_native_episode_manifest.py`](../scenesmith/robot_lab/lerobot_native_episode_manifest.py) |
| Training/evaluation | [M20–M22 roadmap](./autonomous-workflow/09-autonomous-milestones.md) and the relevant T20 brief |
| Historical proof meaning | [proof-state history](./autonomous-workflow/proof-state-history.md) and the linked session/reviewer record |
