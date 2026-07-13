# Slice Brief 074 - Ignore Unselected AVFoundation Sources

**Date:** 2026-07-13

## Objective

Allow fresh camera discovery to include an unselected AVFoundation screen-
capture source while retaining exact, unique system-camera linkage for every
selected physical camera.

## Reproduced failure

Fresh discovery contains the two exact signed physical camera names in both
AVFoundation and the system camera catalog, plus AVFoundation-only
`Capture screen 0`. Candidate construction rejected the whole discovery before
lease use or hardware open because it required equality of the complete name
sets.

## Contract

- Require every system camera name and unique ID to remain unambiguous and to
  appear in AVFoundation discovery.
- Permit extra AVFoundation sources only when they are not selected.
- Continue rejecting selection of any source without exactly one system camera
  identity and reviewed input mode.
- Add deterministic positive and negative regression coverage and run the full
  static-pose proof ladder in both pinned runtimes.

No live session, proof label, motion, model, training, or paid compute authority
is granted by this correction.
