# SceneSmith Domain-Randomized Intervention Task List

This is the sequential implementation list for turning the SO-101 desk-sort
workcell into a domain-randomized, human-correctable simulation system.

## Goal

Run batches of randomized SceneSmith SO-101 sorting episodes in MuJoCo. When an
episode fails or the operator takes over, read a physical SO-101 leader arm as a
safe input device, apply that correction to the simulated robot, and write the
result as LeRobot-compatible intervention data for later fine-tuning.

The physical follower must stay disconnected from this intervention path unless
a separate explicit hardware-enable gate is added and armed.

## Sequential Tasks

### 1. AprilTag Fiducial Contract

- Add first-class fiducials to the `RobotLabScene` schema.
- Default the desk-sort scene to one AprilTag-style marker mounted on a fixed
  calibration plate at the back of the desk.
- Store `family`, `tag_id`, `size_m`, `position_m`, `euler_deg`, and
  `attached_to`.
- Export fiducials into:
  - `scene.json`
  - `scene_state.json`
  - `sim_bridge_contract.json`
  - `lerobot/policy_request.json`
  - `lerobot/lelab_manifest.json`
- Render the tag in MuJoCo and Three.js as visible black/white marker geometry.
- Add a calibration report that records camera visibility expectations and
  ground-truth tag pose.
- Acceptance:
  - MuJoCo loads with `apriltag_0` body/geoms/sites.
  - Viewer includes the visible fiducial.
  - Tests prove metadata and render objects exist.

### 2. Domain Randomization

- Add deterministic randomization from a numeric seed.
- Randomize within bounded ranges:
  - cube initial XY positions
  - tray XY positions
  - cube mass
  - desk color
  - wall/floor color
  - lighting intensity metadata
  - camera noise metadata
  - AprilTag visibility metadata
- Keep all randomized states physically valid and inside the reachable desk
  workcell.
- Write per-episode randomization manifests.
- Acceptance:
  - Same seed produces identical scene variant.
  - Different seeds produce changed cube/tray/appearance parameters.
  - Randomized scene still passes the MuJoCo validator.

### 3. Intervention Supervisor

- Build a closed-loop episode supervisor separate from the legacy scripted smoke
  path.
- Episode phases:
  - `autonomous`
  - `failure_detected`
  - `intervention`
  - `recovered`
  - `accepted`
  - `failed`
- Failure detectors:
  - timeout
  - final scoring failure
  - cube outside matching tray
  - optional forced failure for proof
  - manual intervention request
- Correction sources:
  - `simulated_leader`: deterministic correction source for verification.
  - `physical_leader`: read-only SO-101 leader arm stream through LeRobot.
- Acceptance:
  - Can run a randomized episode with simulated intervention.
  - Summary records failure reason, intervention frames, final score, and seed.

### 4. Leader-Arm Bridge

- Add a leader-only SO-101 bridge.
- Reuse LeRobot/LeLab calibration conventions.
- Connect only to the leader arm.
- Never instantiate or send commands to the physical follower.
- Convert leader actions into SceneSmith/MuJoCo joint targets.
- Provide clear status and error messages for missing hardware.
- Acceptance:
  - `--correction-source simulated_leader` works without hardware.
  - `--correction-source physical_leader` fails safely if no leader port/config is
    supplied.

### 5. Intervention Dataset Export

- Write intervention rollouts into a SceneSmith correction dataset artifact.
- Include LeRobot-compatible PI05 image/state/action keys.
- Preserve extra sidecar metadata:
  - policy action
  - human action
  - `is_intervention`
  - intervention phase
  - failure reason
  - randomization seed
  - AprilTag pose metadata
- Acceptance:
  - Dataset export creates a summary JSON.
  - Frames include correction metadata sidecars.
  - Image sources include side, overhead, and physical wrist-camera views.

### 6. Action Server Integration

- Extend the browser action server with randomized episode controls.
- Add controls for:
  - single randomized episode
  - randomized batch count
  - force-failure proof mode
  - intervention mode
  - visible current seed
- Keep the existing plus-button path working.
- Expose status fields for AprilTag, randomization, and intervention readiness.
- Acceptance:
  - Browser verifier can trigger a randomized intervention episode.
  - Screenshot shows the AprilTag and updated controls.
  - Proof JSON records intervention metadata.

### 7. Documentation And Verification

- Update bridge docs with the AprilTag and intervention contracts.
- Add focused unit tests for:
  - fiducial schema/export
  - deterministic randomization
  - intervention summary/dataset metadata
- Run:
  - unit tests
  - Python compile checks
  - scene generation
  - MuJoCo validation
  - randomized intervention episode
  - action-server verification where practical
- Acceptance:
  - All focused checks pass.
  - Final proof artifacts are named in the closeout.

## Non-Goals For This Pass

- Do not write commands to the physical follower.
- Do not claim full autonomous neural closed-loop sorting if the task controller
  or correction supervisor is completing the recovery.
- Do not require AprilTag detection for policy success.
- Do not require physical leader hardware to verify the software path.
