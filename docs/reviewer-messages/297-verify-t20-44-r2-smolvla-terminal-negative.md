# Reviewer Decision 297 - Verify T20.44 R2 SmolVLA Terminal Negative

**Date:** 2026-07-16

## Decision

`VERIFY_T20_44_R2_SMOLVLA_TERMINAL_NEGATIVE_AND_ROUTE_T20_43B_AFTER_ORIGIN`

The one authorized marker-bound R2 attempt completed its frozen recipe and
independent verification. Result
`9d916206cbbb86b67a42d3449953bc7b272e1de5171996df224e29772369e14f`
is a valid terminal negative, not a runtime failure and not a Gate C pass.

## Reconstructed execution boundary

- Attempt marker: `cb01bcfb5826af2cb9c30d718994872b54a7aa59fc9d11c803744f23f11fc1d8`.
- Run: `3d49f4df8be368392bc9f44fed05b716e468c312232ba8d51fe8dfc3a7c26bf6`.
- Result: `9d916206cbbb86b67a42d3449953bc7b272e1de5171996df224e29772369e14f`.
- Scorecard: `c8d7e3f0249ab2db6b3a90a5e1ef0f7c28b839ec47e8a3851bd3234b0da9c906`.
- Retention receipt: `727b40677e8ea595b8cfb377346a6802f78de2c80d66a1cb27472802b400d938`.
- Exactly one attempt, 5,000 finite optimizer updates, checkpoints
  `[0,500,1000,2500,5000]`, and ten 244-frame policy-owned rollouts completed.
- Every checkpoint evaluated both chunk-50 and receding-10 semantics. Both
  terminal MP4s and manifests exist, and all local checkpoint, rollout, and
  mirror files are byte-bound by the retention receipt.
- The independent `--verify` invocation exits 0 and reconstructs the same
  result identity, counts, first-pass-null state, and terminal status.

## Behavioral result

All ten strict-v2 results are false. No checkpoint is eligible for selection
and T20.40 archive replay remains closed.

The strongest partial interaction occurred at update 1,000 under receding-10:
73 strict-contact frames, 18.061 mm maximum lift, three of eight grasp-hold
frames, and 31 of 64 recording-stable-hold frames. It still missed the 25 mm
lift threshold and the complete strict-v2 phase conjunction. At update 5,000,
chunk-50 reached 5.507 mm lift with five strict-contact frames; receding-10
reached 3.427 mm with six. Neither terminal rollout recorded a grasp-hold
frame. All ten rollouts diverged from the source action at frame zero while
their initial reset state remained exact.

Training plumbing is valid: Gate A passed, all scheduled updates were finite,
all checkpoints and dual-semantics evaluations were retained, and the renderer
failure from T20.43 did not recur. That does not imply learned strict-v2
success, physical transfer, or promotion.

## Adversarial disposition

- The first-pass selector remains null; no partial metric or report-only
  amended/uniform analysis may substitute for strict-v2.
- No active assist, action projection, non-pad contact, hardware, camera,
  serial, network, package installation, external compute, Brev, physical
  motion, transfer, or promotion occurred.
- The marker consumed the sole T20.44 attempt. No retry, replacement,
  checkpoint continuation, correction objective, schedule/threshold change,
  or result rewrite is authorized.
- Large checkpoint, rollout, and video trees remain local and signed; only the
  compact marker/result/scorecard/retention boundary is tracked.

## Route

Owner addendum commit `8b4a206` authorizes exactly one T20.43b ACT replacement
after this T20.44 terminal result, review, and synchronized state are exact on
origin. T20.43b must reuse the stable T20.44 interpreter and real renderer
smoke and retain the unchanged 10,000-update ACT recipe lineage under a fresh
brief, Gate A, composer decision, preflight, permit, and pre-run review.
T20.45 remains pending behind the restored R1 evidence. No T20.43b model or
optimizer action is granted by this review.
