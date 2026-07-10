# Manager Intervention 001 - Finish T16.1 Dependency Pins

**Date:** 2026-07-10

## Decision

`REDIRECT`

## Evidence Anchors

- `100`: `openpi_semantic_reference.revision` is `null` and its resolution is
  `unresolved_remote_reference` in the committed lock.
- `100`: `menagerie_robotstudio_so101.revision` is `null` and its resolution is
  `unresolved_remote_reference` in the committed lock.
- `100`: the lock stores the developer machine's absolute `repo_root`, includes
  it in `identity_sha256`, and rejects an equivalent checkout at another path.
- `75`: commit `92adde5` is still valuable partial work because it correctly
  captures the live LeLab pin, separate dirty LeRobot patch identity, and active
  Robot Studio model hashes.

## Reason

The reviewer interpreted explicit unresolved references as satisfying “pin all
dependencies.” They satisfy truthfulness but not the T16.1 outcome. A dependency
lock must identify the exact external revisions and remain valid when the same
repository is checked out elsewhere.

## Required Correction

1. Resolve OpenPI and Menagerie to exact commits.
2. Record model/reference paths plus license and selected content hashes at those commits.
3. Validate their pin structure offline after lock generation.
4. Remove the absolute checkout path from the signed identity and verification gate.
5. Keep the runtime model unchanged and the split LeRobot state unresolved.

T16.2 remains pending until the corrected T16.1 lock passes review.
