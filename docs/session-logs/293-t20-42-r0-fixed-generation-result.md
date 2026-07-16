# Session Log 293 - T20.42 R0 Fixed Generation Result

## Execution

- The origin-preserved Reviewer 289 acceptance was reverified before the run.
- The immutable marker was written first at
  `2026-07-16T13:10:07-05:00`, consuming the sole permit before candidate
  execution.
- The fixed runner executed all 119 ordered training candidates followed by
  all nine ordered fresh-held-out candidates exactly once. No retry,
  replacement, resampling, seed-6/7 regeneration, or physics randomization
  occurred.
- A first shell timestamp-format invocation failed before marker creation and
  before any output existed; it did not consume the permit. The permit-bound
  invocation above is the sole attempt.

## Result

- All 128 candidates completed without runtime or strict-v2 failure.
- All 119 training candidates entered the training split; all nine fresh-held-
  out successes remained outside training and statistics.
- The exact ten-episode T20.23 base was included once, yielding 129 training
  episodes and 31,366 frames.
- The frame compiler retained 31,232 generated frames in 1,408 hard-boundary
  segments and emitted 59,904 unpadded windows.
- Training-only MEAN_STD statistics are finite and positive for all six action
  and state channels. Existing held-out seeds 6-7 and all nine fresh-held-out
  candidates contributed zero fitted values.
- Result identity `d238379b...`, mixture `37b30d34...`, statistics
  `02ba0e70...`, and retention receipt `19d19fba...` bind the local output
  trees. Large outputs remain local and Git-ignored; compact evidence is
  tracked.

## Verification

- The producer completed with exit 0 and status `verified_success`.
- A separate `--verify` invocation recomputed the complete retained boundary
  and exited 0 with the same result identity and counts.
- A fresh package load recovered exactly 129 episodes and 31,366 frames.
- Adversarial checks confirm base-once inclusion, zero held-out training rows,
  finite positive standard deviations, all prohibited authority fields false,
  and zero output symlinks.

## Proof boundary

This is scripted-expert simulation dataset evidence, not learned-policy,
Gate C, metric-twin, hardware, transfer, or promotion proof. No model was
loaded, no inference or optimizer ran, and no hardware, camera, serial,
network, external-compute, or Brev access occurred. Reviewer 290 accepts R0
and routes to a fresh T20.43/R1 ACT brief.
