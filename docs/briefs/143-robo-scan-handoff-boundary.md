# Slice Brief 143 - Robo Scan Handoff Boundary

**Date:** 2026-07-14

## Objective

Integrate the separately modularized Robo Scan work into the SceneSmith
documentation and architecture as a fail-closed upstream scene-scan,
scene-creation, and calibration-artifact boundary. Make the path discoverable
without importing an unqualified package, copying its dynamic state, or
representing a reference-only scene as a metric physical twin.

## Contract

- Robo Scan remains a separate repository and source of scan/reconstruction
  artifacts. Its current state, evidence, and hardware permissions remain
  authoritative only in its own `GOAL.md` and `project_state.json`.
- Sim-link accepts no automatic filesystem, package, Git, or runtime import
  from Robo Scan. An owner-selected, immutable export manifest is the only
  proposed future handoff.
- A reference-only or synthetic export may support visual context or a
  simulation hypothesis only. It cannot set SO-101 base/world alignment,
  MuJoCo scale, physical-camera calibration, twin qualification, training
  readiness, physical transfer, or promotion eligibility.
- A future metric handoff must bind source revision, canonical artifact
  identities, evidence mode, coordinate convention, camera/depth calibration,
  measured fiducial layout and uncertainty, transforms, and capture provenance;
  it must then pass sim-link validation and central authority composition.

## Acceptance Criteria

- A reader can find the Robo Scan relationship from the documentation hub,
  architecture, requirements index, and decision index.
- A dedicated handoff document makes accepted, rejected, and future artifact
  classes explicit and routes mutable state to the upstream repository.
- Static tests keep the handoff guide linked and prevent an accidental
  `so101_scan` or `environment_scanner` runtime import in sim-link’s governance
  code before a reviewed implementation contract exists.
- State pointers, focused tests, Markdown-link checks, review, and remote
  preservation all pass.

## Out Of Scope

Opening a camera or robot, using a serial port, reading live hardware,
capturing data, importing or vendoring Robo Scan, consuming an upstream
artifact, changing calibration, changing simulation geometry, training,
external compute, Brev, or any physical/twin/promotion authority.
