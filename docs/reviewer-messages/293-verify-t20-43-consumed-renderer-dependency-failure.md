# Reviewer Decision 293 - Verify T20.43 Consumed Renderer Dependency Failure

**Date:** 2026-07-16

## Decision

`VERIFY_T20_43_CONSUMED_RENDERER_DEPENDENCY_FAILURE_NO_RETRY`

## Reviewed boundary

Brief 219; implementation `9a03a86`; authority `2f2a2ca`; signed acceptance
`7d742980...`; origin-confirmed run commit `be30f15`; attempt `064e5650...`;
checkpoint-0 tree `916200d0...`; chunk-50 trace `6133ce58...`; terminal
receipt `b64ec6d0...`; and the exact receipt reconstruction command.

## Findings

- The immutable marker was written at `2026-07-16T15:11:58-05:00` before
  cached-backbone deserialization, ACT construction, inference, or optimizer
  creation and consumed the sole permit.
- The fresh full ACT policy and optimizer were then constructed, checkpoint 0
  was saved, and one unassisted chunk-50 policy-owned rollout completed. It
  failed unchanged strict-v2 with zero strict-contact frames and only
  `3.0422519e-7` m lift. This is an untrained checkpoint-0 diagnostic, not a
  trained ACT capability result.
- The run stopped before receding-10, every trained checkpoint, and the first
  optimizer update. No mirror completed and no full result, scorecard, run
  summary, or retention receipt was written.
- The failure is an exact environment-boundary defect. The reviewed preflight
  proved MuJoCo 3.3.5 in the main isolated runtime, while `_render_mirror`
  launched `external/lerobot/.venv/bin/python`; that child deterministically
  exits 1 on `import mujoco` with `ModuleNotFoundError`. The renderer itself
  therefore never started.
- Terminal receipt `b64ec6d0...` binds the attempt, permit, three immutable
  partial files, 206,494,928-byte model hash, complete trace hash/metrics,
  missing mirror, exact child probe, zero updates, no retry, and every closed
  hardware/network/external-compute authority. Its tracked file hash is
  `661da2f2...`.

## Adversarial disposition

This is neither a Gate C pass nor a trained-policy negative. The run contract
requires all seven checkpoints and both queue variants; those were not
completed. The one-use permit is nevertheless consumed, and fixing the child
interpreter cannot revive or repeat T20.43. No threshold, dataset, recipe,
checkpoint, or policy evidence is changed.

The same dependency class is preventable in the next architecture: a future
preflight must execute the real renderer entrypoint with the exact child
interpreter and verify a nonempty MP4 before its attempt marker. It must also
bind that interpreter/environment rather than proving only the parent process.

## Disposition

Verify T20.43 as a consumed-attempt terminal infrastructure failure and close
R1 with ACT capability unresolved. Per the recorded T20.41 owner route, R2
T20.44 becomes dependency-ready after this boundary is preserved on origin;
open a fresh SmolVLA brief and include the exact renderer smoke before any new
permit. T20.43 has no replacement or retry authority.

## Authority withheld

No T20.43 retry or replacement, optimizer training, checkpoint continuation,
result fabrication, threshold change, correction objective, archive replay,
hardware/camera/serial access, physical motion, network/download, external
compute, Brev, physical transfer, promotion, destructive operation, or R2
model action before a fresh brief and composed authority.
