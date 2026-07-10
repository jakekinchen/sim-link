# Slice Brief 010 - Twin Contract Schemas

## Objective

Complete T16.2 with durable, content-addressed schemas for `TwinProfile`,
`TwinQualificationSpec`, and `TwinQualificationReport`, plus a simulation-only
example bound to the exact robotics dependency lock.

## Required Semantics

Every parameter record supports:

- value and units;
- origin: `read`, `measured`, `CAD`, or `fitted`;
- uncertainty bounds or an explicit unknown state;
- validity conditions such as voltage and temperature;
- evidence artifact/run references.

The profile must distinguish structural model identity, coordinate/gripper
contract, kinematics, inertials, actuators, backlash/friction/compliance,
cameras/timing, gripper/contact, environment/object profiles, and requalification
triggers. Missing physical measurements remain unknown rather than receiving
invented defaults.

The qualification specification must declare held-out metrics, tolerances,
required evidence, and authority level. The report must link the exact profile
and spec identities and record each metric as `pass`, `fail`, or `not_run`.

## Proof States

- `structural_baseline_only`
- `simulation_only`
- `physical_qualified`

A report may not claim `physical_qualified` when any required physical metric is
missing, failed, simulated-only, or lacks evidence.

## Acceptance

- All three artifacts have schema versions and canonical identity hashes.
- Validation rejects invalid units/origins, reversed uncertainty bounds,
  impossible proof/status combinations, missing dependency-lock linkage, and
  stale/tampered identities.
- The checked-in example is explicitly `simulation_only`, physically unqualified,
  and references `pi05_robotics_dependency_lock.json` by path and identity hash.
- A CLI can emit/verify the example deterministically.
- Focused and broader robot-lab tests pass.

## Boundaries

- Do not switch MJCF/URDF runtime inputs.
- Do not claim real calibration or physical qualification.
- Do not read a serial bus, command motion, start training, or invent measured masses.
