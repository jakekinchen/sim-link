# Session 104 - Unselected AVFoundation Source Correction

**Date:** 2026-07-13

Fresh discovery `4c29fe9c...` contained the exact RealSense and C922 in both
AVFoundation and the system camera catalog, plus AVFoundation-only
`Capture screen 0`. The first candidate build failed before contract issuance,
serial/camera open, or immutable session evidence. The lease/profile existed
only as expired preflight artifacts and sessions started remained zero.

Brief 074 allows additional unselected AVFoundation sources while requiring
every system camera name and unique ID to remain unambiguous and every selected
source to map to exactly one system identity. Static-pose resolution filters
the discovery candidates before matching the two signed stable hashes.

Actual fresh discovery now builds candidate preflight `f8555cad...`, resolving
RealSense index 0 and C922 index 1 with `hardware_accessed=false`. Verification
passed 78 focused tests in each pinned runtime, 378 broad authority/twin tests
in 122.702 seconds, both source verifiers in both runtimes, and diff checks.
No serial/camera opened, no physical command occurred, and training stayed
locked.
