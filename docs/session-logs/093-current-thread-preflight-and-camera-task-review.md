# Session 093 - Current-Thread Preflight And Camera/Task Review

**Date:** 2026-07-12

Formal hardware-profile capture for thread
`019f5804-b684-7023-a599-4f803ac0aceb` rejected with `ValueError: Active Codex
thread is not using on-request approval`. The check failed before `codex
doctor`, lease issuance, discovery, holder census, candidate-contract issuance,
or device open. No USB, serial, camera, servo bus, Studio, model, policy,
simulation, optimizer, training, motion, or paid compute path ran. The live gate
remained closed with sessions-started zero.

Offline visual review used the already accepted T16.5b frame bytes. Stable
RealSense `69d55167...` frame `c77e4c7e...` shows the gripper jaws from the
camera viewpoint. Stable C922 `9931d030...` frame `caab2f5d...` shows the full
arm and the RealSense physically attached at the wrist. The reviewed binding is
therefore RealSense to `observation.images.wrist` / checkpoint
`observation.images.left_wrist_0_rgb`, and C922 to
`observation.images.top` / checkpoint `observation.images.base_0_rgb`. Numeric
camera indexes are not part of the decision. This reverses the fixture
hypothesis.

The existing sorting checkpoint prompt is pinned byte-for-byte as `Sort each
cube into the same-colored tray: red cubes into the red tray and blue cubes
into the blue tray.` Its UTF-8 SHA-256 is `6bf96b1858409892...`. Neither the
role decision nor prompt is issued as a production PI0.5 reviewed input because
the required accepted live-session review decision does not exist.

The existing reviewed-input artifact independently verifies in both pinned
runtimes and remains `blocked_missing_reviewed_inputs`. Thirty-four focused
tests pass in each runtime. The broad offline authority/twin gate passes 376
tests in 92.437 seconds. Canonical JSON parsing and `git diff --check` pass.
