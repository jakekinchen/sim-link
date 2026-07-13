# Slice Brief 098 - Explicit-Pad Proxy Search

**Date:** 2026-07-13

## Objective

Correct the single collision-occlusion cause established by Brief 097 and rerun
the exact same geometry-first design.

## Contract

- Create a separately versioned proxy-contact model in which the original fixed
  and moving composite jaw meshes remain present and auditable but have contact
  masks disabled.
- Keep only the two explicit fingertip pad boxes contact-active for jaw/object
  qualification; keep servo shell and every other non-pad geom excluded.
- Preserve all 12 training candidates, the untouched holdout, ranges, seeds,
  trajectory, friction, compliance, mass, contact time constants, evaluator,
  and selection order from Brief 097.
- Report whether pad contact becomes reachable and whether strict-v2 geometry
  persists through the table-level hold. Do not infer success from contact count
  alone.

This slice may establish or reject the fingertip collision proxy. It may not
claim a full dynamic grasp, training readiness, physical calibration, or motion.

## Verified Outcome

- The identical 12-candidate design plus untouched holdout was rerun with only
  explicit pad boxes contact-active on the jaws.
- Three reachable candidates produced 277 raw fixed-pad contacts with positive
  forces up to 4.337551107 N. No moving-pad contact occurred, so no bilateral
  representative or strict-v2 witness formed.
- The holdout remained ineligible and excluded from selection.
- This proves the proxy path is active while isolating the next error to
  object targeting relative to the pad midpoint: the current gripperframe
  target is near the fixed fingertip rather than between both pads.
- Artifact identity: `015b605ea2c148aa59064b09126e280d829e9be8267ecb6235f603b8bcbfe715`.
- File SHA-256: `e21a82d16c6e668b6dc9e06e8cf8b2360025c30b4ecdb6f0d584cfecf31a1d8e`.
- Eight focused tests pass in each pinned runtime; the 180-test broad gate
  passes.
