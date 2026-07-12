# Session 091 - Static-Pose Preflight Runtime Ambiguity

**Date:** 2026-07-12

The remotely preserved one-session gate at `f5b6033` was exercised only through
its first formal preflight call. `capture_hardware_execution_profile_evidence`
rejected before USB/serial/camera discovery because the rollout contained three
session metadata records and concurrent active turn IDs. The earlier current
goal turn recorded `on-request`/`danger-full-access`; a later concurrently
active turn recorded `never`/`danger-full-access`.

The failure occurred before discovery, holder enumeration, lease issuance,
candidate-contract issuance, private-destination creation, or the started
session boundary. No hardware was enumerated or opened; no servo bus, camera,
model, policy, replay, optimizer, training, or paid-compute path ran. No private
session outcome artifact exists. Reviewer Decision 087 closes the gate with
sessions-started zero and leaves every proof label withheld.

Thirty-four focused tests pass in each pinned robotics runtime. The strict
duplicate-key/canonical-state audit proves the gate closed with zero sessions,
`git diff --check` passes, and the 374-test broad offline authority/twin gate
passes in 104.406 seconds.
