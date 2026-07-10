# Executor Session 030 - Vendor Menagerie Structural Source

**Date:** 2026-07-10

## Slice

Resolve the T16.3 source prerequisite without changing the active runtime model.

## Result

- Added Menagerie `robotstudio_so101` license, README, `so101.xml`, and `scene.xml`
  from commit `71f066ad0be9cd271f7ed58c030243ef157af9f4`.
- Bound local files to their upstream paths, sizes, and SHA-256 values in the
  robotics dependency lock.
- Added drift/missing-file tests and refreshed dependent twin artifact identities.
- No binary assets, runtime model switch, training, or hardware access occurred.

## Verification

- All four vendored hashes match the committed remote pins.
- Eight dependency-lock tests pass.
- Ninety-five combined twin/dependency/scene/autolearn/intervention/guard tests pass.

## Commit

`38b3425 feat(robot-lab): vendor pinned Menagerie twin source`
