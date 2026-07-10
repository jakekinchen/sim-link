# Slice Brief 012 - Resume Structural Twin Diff

## Objective

Complete T16.3 using the active Robot Studio MJCF and the newly tracked, exact-
commit Menagerie `so101.xml`; do not switch runtime inputs.

## Source Inputs

- Active runtime path/hash from `pi05_robotics_dependency_lock.json`.
- Menagerie vendored root/files from the same lock.
- Twin profile identity from the checked-in simulation-only profile.

## Acceptance

- Emit a content-addressed machine diff with separate matched, mismatched,
  missing, extra, and unknown records.
- Cover inertials/COM, joints/limits/frames, actuators/force/gains, arm collisions,
  gripper collisions/contact parameters, cameras, solver settings, friction,
  backlash declaration/attachment, and named sites including `gripperframe`.
- Record numeric deltas where meaningful, including wrist-roll limit and
  gripper-frame transform.
- Prove source hashes before parsing and reject source/artifact tampering.
- CLI write/verify and focused/broader tests pass.
- Record a reconciliation decision: adopt, adapt, or retain each difference;
  do not silently replace the runtime model.

## Boundaries

- Do not copy mesh assets or make Menagerie selectable in this slice.
- Do not modify current scene exports, checkpoints, training data, or hardware.
