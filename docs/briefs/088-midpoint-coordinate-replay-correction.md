# Slice Brief 088 - Midpoint Coordinate Replay Correction

**Date:** 2026-07-13

## Objective

Correct the exact offline coordinate-projection and false self-collision exposed
by Reviewer 113 without changing the legacy simulation-policy dataset contract
or weakening any physical gate.

## Contract

- Preserve `scenesmith.so101_coordinates.v1` and its existing offset mapping as
  the legacy simulation-policy dataset coordinate contract.
- Add one separately versioned, fail-closed midpoint-direct candidate for the
  pinned `so101_new_calib.xml` model. Bind the shared zero semantics documented
  by the physical LeRobot calibration profile and the pinned model; keep its
  use limited to offline physical-pose and proposal diagnostics.
- Reject non-finite, wrong-width, and out-of-model-range inputs by default.
  Any diagnostic projection must be explicit and observable.
- Reproduce the measured `q_after` across the finite sign/offset candidates,
  bind calibration-range and articulated-frame evidence, and select at most one
  candidate for diagnostic replay.
- Replay the existing immutable PI0.5 proposal at horizons 5, 10, and 15 twice
  in the pinned MuJoCo scene. Record projection, contacts, velocities, warnings,
  and exact determinism.
- Keep scene mismatch, checkpoint-support mismatch, proposal magnitude, policy
  input validity, and all authority decisions independent from coordinate-pose
  representability.

This slice may establish only that the measured physical pose and proposal are
reproducible under a source-backed midpoint coordinate candidate for offline
diagnosis. It must not grant matched replay, accepted shadow, positive actuation
recommendation, physical motion, twin qualification, training, or paid compute.
