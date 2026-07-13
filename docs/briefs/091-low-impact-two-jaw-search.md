# Slice Brief 091 - Low-Impact Two-Jaw Search

**Date:** 2026-07-13

## Objective

Search a finite object-relative wrist-roll and vertical pregrasp grid for
simultaneous fixed- and moving-jaw contact below the strict impact limit, then
test the selected candidate through an unassisted lift and hold.

## Contract

- Keep the nominal anchor, pinned model, seed, initial pose, close target, and
  controller fixed except for the declared finite wrist-roll/height grid.
- Require simultaneous `gripper` and `moving_jaw_so101_v1` contact in the same
  MuJoCo frame; aggregated contacts do not count.
- Rank only candidates whose peak close force remains at or below 5 N.
- Validate the selected contact with no weld, equality assist, teleport, or
  scripted object motion during lift and hold.
- Record joint-domain closure values, but keep metric fingertip aperture
  incomplete until a geometry-derived mapping exists.
- Preserve a dropped or slipped object as a rejected result.

This slice may establish a low-impact two-jaw contact candidate and its
unassisted-lift result. It may not establish strict grasp, calibrated aperture,
policy success, training readiness, physical qualification, or motion authority.

## Verified Outcome

- Twenty fixed-grid candidates were executed against the exact Brief 090 model
  and nominal object.
- The selected candidate uses wrist roll -1.5 rad and a 0.018 m object-relative
  pregrasp height. It produces 11 two-jaw close frames and all 8 two-jaw hold
  frames while peak contact remains 4.1971684 N.
- The selected lift validation is exact across two runs and uses no weld or
  other contact assistance. It retains two-jaw contact for 4 lift frames, then
  slips; the 12-frame lift hold has zero two-jaw frames and ends at table height
  0.324974 m.
- The two-jaw contact range is 0.2395 to 16.724525 gripper percent. This is joint
  domain evidence, not a metric aperture profile.
- Artifact identity: `5a5de249f7374cde37b6e201a4ae4097ee74e0f39bf7884c205947e8cf7446e2`.
- File SHA-256: `fa250ee649cbbae1cefe5841cd0a6f049070628f82e9a27fa9fdfaf21d50f732`.
