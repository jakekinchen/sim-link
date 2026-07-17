# Session 323 - T20.43c-R2 Terminal Negative

**Date:** 2026-07-17
**Task:** T20.43c-R2 / Brief 229
**Reviewer:** 318

## Outcome

The manual ACT-on-R0 replacement started at `2026-07-16T23:21:49-05:00` and
completed its unchanged 10,000-update recipe exactly once. Independent
`--verify` reconstruction passes. Final receipt `be11a258...` binds marker
`dfe3ff05...`, equivalence `fdc06297...`, result `bf2c8b46...`, retention
`e565e17a...`, and the immutable prior interruption `d848a1a8...`.

All seven checkpoints were evaluated under chunk-50 and receding-10. None of
the 14 rollouts passed strict-v2 Gate C. The result is therefore a verified
terminal negative with no retry, not an infrastructure failure.

## Strongest behavior

The negative is a one-predicate near-miss under chunk-50. At update 10,000 the
policy achieved 8/8 grasp-hold frames, 24/24 unassisted-lift frames, 12/12
unsupported-hold and support-free frames, 64/64 stable-hold frames, 24/24 lower
frames, and 37.655 mm maximum lift. The sole failed predicate was final release
clearance. Update 7,500 had the same sole failure with 40.025 mm lift. The
maximum observed lift was 45.674 mm at update 2,500 receding-10, but that route
missed multiple frame/clearance gates. Receding-10 at update 10,000 retained no
strict grasp hold and lifted only 0.502 mm.

No terminal-failure receipt exists. No hardware, camera, serial, physical
motion, network, package installation, external compute, or Brev action
occurred. Training is closed, Gate C remains failed, and the release-phase
counterexample is the exact transfer lesson for the fork.
