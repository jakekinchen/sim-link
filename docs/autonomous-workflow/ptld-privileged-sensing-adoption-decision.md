# PTLD-Inspired Privileged Sensing Adoption Decision

**Date:** 2026-07-12

**Decision:** Adopt the instrumented-cell and privileged-supervision paradigm as
a future adjunct to M19 physical twin identification and as a separately gated
M21 deployment-observer experiment. Do not treat latent distillation as simulator
calibration, import a tactile-specific runtime, or run a teacher policy on the
physical SO-101 under the current authority.

## Source pin

- Paper: [PTLD: Sim-to-real Privileged Tactile Latent Distillation for
  Dexterous Manipulation](https://arxiv.org/abs/2603.04531), arXiv:2603.04531,
  inspected 2026-07-12.
- Project page: <https://akashsharma02.github.io/ptld-website/>.
- The inspected method trains a privileged policy in simulation, uses calibrated
  cameras and object markers to expose noisy object pose in an instrumented real
  cell, records paired privileged latents and real tactile observations, and
  distills a tactile-plus-proprioceptive deployment encoder. Its iterative DAgger
  collection is an on-policy physical-data procedure, not a read-only calibration
  operation.

No paper code, model, checkpoint, tactile runtime, or hardware asset is imported
by this decision. The method is adopted only as an architectural reference.

## Current-system compatibility

The current SO-101 lane is not a literal PTLD implementation:

- Reviewer 089 maps the rigid wrist-mounted RealSense and external C922 workcell
  overview to the intended PI0.5 wrist and base image keys. That decision is not
  yet a production-issued same-session input binding, and the cameras are not a
  jointly calibrated multi-view object-pose truth system.
- Accepted T16.5b evidence proves exact camera identity, finite 640x480 capture,
  read-only servo census, and cleanup. It does not prove synchronized capture,
  camera intrinsics or extrinsics, marker tracking, object pose, end-effector
  pose, or contact state.
- The current follower has no repo-bound tactile-array observation contract.
  Motor-current, force, or future tactile inputs cannot be assumed or silently
  substituted.
- T16.5c remains the active no-actuation static-pose, preprocessing, policy-shadow,
  and matched-replay prerequisite. The training lock remains closed, and this
  decision does not change whatever finite live-gate state the authoritative
  project state records.
- The only conditionally confirmed initial motion is the existing no-op-equivalent
  then one-small-joint-delta-and-return permit after all prerequisites pass. It
  does not authorize task motion, contact, teacher-policy actuation, or DAgger.

## Component disposition

| Component | Disposition | Reason |
|---|---|---|
| Instrumented real cell with privileged object and robot state | Adopt for future M19 evidence | It can supply metric, uncertainty-bearing observations for camera, kinematic, timing, actuator, and contact identification. |
| Explicit real-to-sim parameter fitting and held-out prediction | Required | Physical twin qualification needs interpretable fitted parameters and held-out real behavior inside the simulated envelope. |
| Privileged latent or state distillation into deployment sensors | Evaluate in M21 | It may improve a visual-proprioceptive observer after the twin, experience, mixture, and competence gates pass. |
| Literal tactile PTLD | Defer | No current tactile-array hardware, source contract, calibration, preprocessing, or deployment interface exists. |
| PTLD PPO/AAC training architecture | No direct adoption | The pinned PI0.5/LeRobot program has a different policy and optimizer contract; replacing it would reopen the executable-stack and training-authority chain. |
| Teacher-policy physical rollout or DAgger | Reject under current authority | It requires repeated on-policy physical actuation and potentially contact, far beyond T16.5c and the initial T16.6 permit. |
| Latent loss as twin-calibration or qualification evidence | Reject | A task latent can match while camera, timing, dynamics, friction, contact, or uncertainty remain physically wrong. |

## M19 instrumented-cell calibration contract

M19 must first use privileged instrumentation for explicit system identification.
The calibration lane has this directional flow:

```text
authorized physical measurements
  -> synchronized privileged-state capture
  -> explicit parameter posterior with uncertainty
  -> held-out real-versus-sim predictive evaluation
  -> TwinProfile and TwinQualificationReport inputs
  -> central authority composition
```

The future capture contract must bind, at minimum:

- session, robot, structural-twin, calibration, object, workspace, camera, marker,
  executable-stack, and authority identities;
- one monotonic clock model, per-source timestamps, measured clock offsets and
  uncertainty, dropped-frame facts, and maximum alignment error;
- requested, projected, sent, and measured actions as separate fields;
- measured joint state and any independently authorized current, force, contact,
  or tactile observations without fabricating unavailable modalities;
- raw deployment-camera frames separately from privileged tracker outputs;
- object, tray, robot-base, gripper, and end-effector poses with coordinate-frame
  lineage, covariance or confidence, visibility, and rejection reasons;
- controller owner, control mode, proof mode, task phase, prompt, and whether any
  action or label used privileged information;
- immutable calibration-fit, development, and held-out session/object splits.

Calibration and identification must produce explicit values or distributions for
the applicable M19 properties: intrinsics, extrinsics, joint offsets, kinematics,
camera and control latency, actuator delay and saturation, settling, backlash,
friction, compliance, gripper aperture/contact geometry, and object/contact
profiles. Each result must record units, uncertainty, validity conditions,
identifiability limits, consumed evidence, and requalification triggers.

The fitted posterior may center and bound later domain-randomization levels. The
held-out panel must not be used to tune that posterior or randomization ranges.
Failure to identify a parameter remains an explicit unknown or conservative
prior; it is never converted into a false point estimate.

## M21 deployment-observer experiment

Only after M19 qualification, M17-M18 data gates, M20 strict competence, and a
separately opened training gate may the repo evaluate a PTLD-inspired observer.
The initial experiment is auxiliary and cannot command the robot.

The teacher side may consume simulator-exact state or instrumented-cell labels,
including object/tray/gripper relative pose and task progress. The student side
may consume only the deployment contract: approved wrist and overview RGB,
proprioception, prompt/task context, and any future independently qualified local
sensor. Tracker poses, markers decoded as poses, simulator state, future progress,
reward, evaluator labels, and teacher latents are supervision only and cannot be
actor inputs.

The experiment must compare at least:

1. The existing deployment observation baseline.
2. A state-target observer trained on explicit privileged labels.
3. A latent-target observer, if a source-bound teacher latent exists.

Evaluation must use held-out sessions and objects and report pose/progress error,
temporal drift, calibration sensitivity, occlusion behavior, uncertainty or
abstention quality, and downstream strict-policy effect separately. A lower
distillation loss alone is not acceptance evidence. Observer acceptance grants
only `deployment_observer_distillation_valid`; policy integration, physical
transfer, actuation, promotion, and twin qualification remain separate decisions.

Iterative DAgger or teacher-policy data aggregation remains a later, separately
authorized option. It requires a preregistered physical safety envelope, contact
authority when applicable, controller/action provenance, deadman and watchdog
proof, bounded collection budget, and explicit separation of teacher, student,
assisted, and autonomous physical outcomes.

## Authority invariants

The new component capabilities may include:

- `instrumented_privileged_state_capture_valid`;
- `physical_parameter_posterior_fit_valid`;
- `held_out_real_sim_prediction_valid`;
- `deployment_observer_distillation_valid`.

None may directly set `simulation_training_ready`, `physical_twin_qualified`,
`physical_transfer_ready`, `promotion_eligible`, or any motion authority. Only
the central composer may derive system-level decisions from the complete,
fresh, subject-matched prerequisite set.

The following fail closed:

- missing or ambiguous clock, coordinate-frame, camera, marker, object, action,
  controller-owner, or authority identity;
- using the same session, trajectory, or object in both posterior fitting and
  held-out qualification;
- deriving a physical parameter solely from a task latent without an explicit
  observation model and held-out predictive test;
- tracker, simulator, evaluator, future, reward, or teacher information entering
  deployment actor inputs;
- relabeling static, fixture, synthetic, replay, teacher-assisted, or
  controller-assisted evidence as autonomous physical evidence;
- self-authorizing motion, contact, training, transfer, or global qualification
  from a capture, fit, observer, or distillation artifact.

## Authority and timing

This decision changes future M19 and M21 acceptance criteria only. It does not
change active T16.5c, create a current dependency, open the training or live
hardware gates, authorize a camera or serial open, permit motion or contact, run
policy inference or MuJoCo, adopt a new runtime or checkpoint, or start paid
compute.

When M19 becomes dependency- and authority-ready, T19.2a must turn the capture
requirements above into a signed machine-readable contract before physical
identification trajectories are collected. T19.3-T19.5 then fit explicit
parameters and qualify them on held-out evidence. T21.2a evaluates the optional
observer only after its own prerequisites pass.
