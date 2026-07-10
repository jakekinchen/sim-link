# Executor Session 017 - Proof-mode Separation

**Date:** 2026-07-10

## Slice

Complete T12.2 by making strict neural control an actual runtime mode and
separating it from contact stabilization, task-space assistance, human takeover,
and physical-robot evidence.

## Result

- `grasp_assist_mode=none` disables contact-gated grasp activation entirely.
- Baseline and candidate evaluation stages now use `none`; DAgger collection
  continues to use the explicitly assisted tray-transfer mode.
- Episodes are classified as strict neural, contact stabilized, controller
  assisted, human intervened, physical robot, scripted invalid, or unproven.
- Evaluation summaries count each proof mode.
- Promotion requires every baseline/candidate episode to match the configured
  strict proof mode even when a caller otherwise allows contact stabilization.

## Verification

- 61 intervention/autolearn tests pass.
- Classifier tests distinguish strict, stabilized, controller, and physical episodes.
- A contact-stabilized 4/4 candidate is rejected by a strict promotion gate.
- Cycle dry-run confirms baseline/candidate argv use `--grasp-assist-mode none`.
- The prior seed-7300 smoke had zero activations/controllers and classifies strict;
  it still failed terminally, which remains honest strict evidence.

## Proof Boundary

No physical-robot evaluation was run. `physical_robot` is a classification and
gate for future evidence, not a claim of hardware success.

## Next Step

T12.3 rotating development and locked audit seed registries.
